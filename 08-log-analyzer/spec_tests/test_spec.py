"""Checks for project 08. Run from the project folder: python -m pytest spec_tests -v"""

import inspect
import itertools
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import analyze

ANALYZE = Path(__file__).resolve().parent.parent / "analyze.py"

LOG_LINES = [
    '10.0.0.1 - - [18/Oct/2026:14:02:11 +0000] "GET /products/42 HTTP/1.1" 200 5123 0.084',
    '10.0.0.2 - - [18/Oct/2026:14:15:00 +0000] "GET /products/42 HTTP/1.1" 200 100 0.050',
    '10.0.0.1 - - [18/Oct/2026:14:30:00 +0000] "POST /cart HTTP/1.1" 500 0 1.200',
    "this line is garbage",
    '10.0.0.3 - - [18/Oct/2026:15:05:00 +0000] "GET /missing HTTP/1.1" 404 0 0.010',
    '10.0.0.1 - - [18/Oct/2026:15:10:00 +0000] "GET /cart HTTP/1.1" 500 0 0.900',
    '10.0.0.9 - - [18/Foo/2026:15:20:00 +0000] "GET / HTTP/1.1" 200 10 0.010',
    '10.0.0.2 - - [18/Oct/2026:16:00:00 +0000] "GET / HTTP/1.1" 200 2048 0.020',
]


def utc(hour, minute=0, second=0):
    return datetime(2026, 10, 18, hour, minute, second, tzinfo=timezone.utc)


@pytest.fixture
def log_file(tmp_path):
    path = tmp_path / "access.log"
    path.write_text("\n".join(LOG_LINES) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def entries(log_file):
    return list(analyze.parse_lines(log_file))


def pairs(items):
    return [tuple(item) for item in items]


def run_cli(*args):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, str(ANALYZE), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        env=env,
    )


class TestParsing:
    def test_parse_valid_line(self):
        entry = analyze.parse_line(LOG_LINES[0])
        assert entry.ip == "10.0.0.1"
        assert entry.timestamp == utc(14, 2, 11)
        assert entry.method == "GET"
        assert entry.path == "/products/42"
        assert entry.protocol == "HTTP/1.1"
        assert entry.status == 200
        assert entry.size == 5123
        assert entry.response_time == pytest.approx(0.084)

    def test_parse_line_ignores_trailing_newline(self):
        assert analyze.parse_line(LOG_LINES[0] + "\n") == analyze.parse_line(LOG_LINES[0])

    @pytest.mark.parametrize("line", [LOG_LINES[3], LOG_LINES[6], "", '1.2.3.4 - - [x] "GET"'])
    def test_parse_malformed_line(self, line):
        assert analyze.parse_line(line) is None

    def test_parse_lines_is_a_generator(self):
        assert inspect.isgeneratorfunction(analyze.parse_lines)

    def test_parse_lines_skips_and_counts_malformed(self, log_file):
        stats = {}
        entries = list(analyze.parse_lines(log_file, stats))
        assert len(entries) == 6
        assert stats["malformed"] == 2


class TestFilters:
    def test_filter_status(self, entries):
        assert [e.path for e in analyze.filter_status(entries, 500)] == ["/cart", "/cart"]

    def test_filter_time_since_inclusive_until_exclusive(self, entries):
        result = analyze.filter_time(entries, since=utc(14, 30), until=utc(15, 10))
        assert [e.timestamp for e in result] == [utc(14, 30), utc(15, 5)]

    def test_filter_time_open_ended(self, entries):
        assert len(list(analyze.filter_time(entries, since=utc(15)))) == 3
        assert len(list(analyze.filter_time(entries, until=utc(15)))) == 3
        assert len(list(analyze.filter_time(entries))) == 6

    def test_filters_are_generators(self, entries):
        assert inspect.isgenerator(analyze.filter_status(entries, 200))
        assert inspect.isgenerator(analyze.filter_time(entries, since=utc(14)))

    def test_filters_are_lazy(self, entries):
        endless = itertools.cycle(entries)
        errors = analyze.filter_status(analyze.filter_time(endless, since=utc(15)), 500)
        assert next(errors).path == "/cart"


class TestReport:
    @pytest.fixture
    def report(self, entries):
        return analyze.build_report(entries, top=5)

    def test_total_and_status_counts(self, report):
        assert report["total"] == 6
        assert report["status_counts"] == {200: 3, 500: 2, 404: 1}

    def test_top_paths_and_ips(self, report):
        assert pairs(report["top_paths"]) == [("/cart", 2), ("/products/42", 2), ("/", 1), ("/missing", 1)]
        assert pairs(report["top_ips"]) == [("10.0.0.1", 3), ("10.0.0.2", 2), ("10.0.0.3", 1)]

    def test_top_limits_the_lists(self, entries):
        report = analyze.build_report(entries, top=1)
        assert pairs(report["top_paths"]) == [("/cart", 2)]
        assert pairs(report["top_ips"]) == [("10.0.0.1", 3)]

    def test_response_times(self, report):
        assert report["avg_response_time"] == pytest.approx(2.264 / 6)
        assert report["p95_response_time"] == pytest.approx(1.2)

    def test_p95_uses_nearest_rank(self, entries):
        template = entries[0]
        many = [
            analyze.LogEntry(**{**vars_of(template), "response_time": t / 100})
            for t in range(1, 21)
        ]
        assert analyze.build_report(many)["p95_response_time"] == pytest.approx(0.19)

    def test_requests_per_hour(self, report):
        assert report["requests_per_hour"] == {
            "2026-10-18 14:00": 3,
            "2026-10-18 15:00": 2,
            "2026-10-18 16:00": 1,
        }

    def test_top_error_paths(self, report):
        assert pairs(report["top_error_paths"]) == [("/cart", 2)]

    def test_accepts_a_generator(self, log_file):
        report = analyze.build_report(analyze.parse_lines(log_file))
        assert report["total"] == 6

    def test_empty_input(self):
        report = analyze.build_report([])
        assert report["total"] == 0
        assert report["avg_response_time"] == 0.0
        assert report["p95_response_time"] == 0.0


def vars_of(entry):
    fields = ["ip", "timestamp", "method", "path", "protocol", "status", "size", "response_time"]
    return {name: getattr(entry, name) for name in fields}


class TestCommandLine:
    def test_json_report(self, log_file):
        result = run_cli(log_file, "--format", "json")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["total"] == 6
        assert report["malformed"] == 2
        assert report["status_counts"] == {"200": 3, "500": 2, "404": 1}
        assert pairs(report["top_paths"])[0] == ("/cart", 2)

    def test_status_filter(self, log_file):
        report = json.loads(run_cli(log_file, "--status", "500", "--format", "json").stdout)
        assert report["total"] == 2

    def test_top_option(self, log_file):
        report = json.loads(run_cli(log_file, "--top", "1", "--format", "json").stdout)
        assert len(report["top_paths"]) == 1

    def test_since_and_until(self, log_file):
        since = json.loads(run_cli(log_file, "--since", "2026-10-18T15:00:00", "--format", "json").stdout)
        until = json.loads(run_cli(log_file, "--until", "2026-10-18T15:00:00", "--format", "json").stdout)
        assert since["total"] == 3
        assert until["total"] == 3

    def test_text_report(self, log_file):
        result = run_cli(log_file)
        assert result.returncode == 0, result.stderr
        assert "/cart" in result.stdout

    def test_missing_file(self, tmp_path):
        result = run_cli(tmp_path / "nope.log")
        assert result.returncode == 1
        assert result.stderr.strip(), "Print the error message to stderr"
        assert "Traceback" not in result.stderr

    def test_help_describes_every_option(self):
        result = run_cli("--help")
        assert result.returncode == 0
        for option in ["--top", "--status", "--since", "--until", "--format"]:
            assert option in result.stdout
