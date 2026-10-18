"""Checks for project 11. Run from the project folder: python -m pytest spec_tests -v

A tiny web server runs on 127.0.0.1 during the checks:
  /file/<n>   a ~40 KB file
  /slow/<n>   the same, after a 0.3 s delay (used to measure concurrency)
  /missing    404
"""

import asyncio
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import download

DOWNLOAD = Path(__file__).resolve().parent.parent / "download.py"
UNREACHABLE = "http://127.0.0.1:9/nothing-listens-here"


def payload(n):
    return (f"file number {n}\n" * 3000).encode()


class Server:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0
        self.requests = 0
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                with server.lock:
                    server.requests += 1
                parts = self.path.strip("/").split("/")
                if len(parts) == 2 and parts[0] in ("file", "slow"):
                    if parts[0] == "slow":
                        with server.lock:
                            server.active += 1
                            server.max_active = max(server.max_active, server.active)
                        time.sleep(0.3)
                        with server.lock:
                            server.active -= 1
                    body = payload(parts[1])
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def reset(self):
        with self.lock:
            self.active = self.max_active = self.requests = 0

    def url(self, path):
        return self.base + path


@pytest.fixture(scope="module")
def server():
    srv = Server()
    yield srv
    srv.httpd.shutdown()


@pytest.fixture(autouse=True)
def fresh_counts(server):
    server.reset()


def run_mode(mode, urls, out_dir, workers=4, force=False):
    if mode == "sequential":
        return download.download_sequential(urls, out_dir, force=force)
    if mode == "threads":
        return download.download_threaded(urls, out_dir, workers, force=force)
    return asyncio.run(download.download_async(urls, out_dir, workers, force=force))


MODES = ["sequential", "threads", "async"]


def file_contents(directory):
    return {p.name: p.read_bytes() for p in Path(directory).iterdir() if p.is_file()}


class TestSafeFilename:
    def test_safe_characters_only(self):
        for url in [
            "https://picsum.photos/seed/1/800/600",
            "https://example.com/a file?x=1&y=2#frag",
            "http://example.com/",
        ]:
            assert re.fullmatch(r"[A-Za-z0-9._-]+", download.safe_filename(url)), url

    def test_deterministic(self):
        url = "https://picsum.photos/seed/1/800/600"
        assert download.safe_filename(url) == download.safe_filename(url)

    def test_unique(self):
        urls = [
            "https://picsum.photos/seed/1/800/600",
            "https://picsum.photos/seed/2/800/600",
            "https://example.com/data?page=1",
            "https://example.com/data?page=2",
            "https://example.com/a/b",
            "https://example.com/a_b",
        ]
        assert len({download.safe_filename(u) for u in urls}) == len(urls)


@pytest.mark.parametrize("mode", MODES)
class TestEveryMode:
    def test_downloads_every_file(self, server, tmp_path, mode):
        urls = [server.url(f"/file/{n}") for n in range(6)]
        report = run_mode(mode, urls, tmp_path)
        assert sorted(report.succeeded) == sorted(urls)
        assert report.failed == {}
        contents = file_contents(tmp_path)
        assert sorted(contents.values()) == sorted(payload(n) for n in range(6))
        for url in urls:
            assert (tmp_path / download.safe_filename(url)).exists()

    def test_failures_are_reported_not_raised(self, server, tmp_path, mode):
        good = [server.url("/file/1"), server.url("/file/2")]
        bad = [server.url("/missing"), UNREACHABLE]
        report = run_mode(mode, [good[0], *bad, good[1]], tmp_path)
        assert sorted(report.succeeded) == sorted(good)
        assert set(report.failed) == set(bad)
        assert all(isinstance(msg, str) and msg for msg in report.failed.values())

    def test_existing_files_are_skipped(self, server, tmp_path, mode):
        urls = [server.url(f"/file/{n}") for n in range(3)]
        run_mode(mode, urls, tmp_path)
        server.reset()
        report = run_mode(mode, urls, tmp_path)
        assert sorted(report.skipped) == sorted(urls)
        assert report.succeeded == []
        assert server.requests == 0

    def test_force_downloads_again(self, server, tmp_path, mode):
        urls = [server.url(f"/file/{n}") for n in range(3)]
        run_mode(mode, urls, tmp_path)
        report = run_mode(mode, urls, tmp_path, force=True)
        assert sorted(report.succeeded) == sorted(urls)

    def test_progress_counts_every_url_once(self, server, tmp_path, mode, capsys):
        urls = [server.url(f"/file/{n}") for n in range(5)] + [server.url("/missing")]
        run_mode(mode, urls, tmp_path)
        counters = re.findall(r"\[(\d+)/6\]", capsys.readouterr().out)
        assert sorted(map(int, counters)) == [1, 2, 3, 4, 5, 6]


def test_all_modes_produce_identical_files(server, tmp_path):
    urls = [server.url(f"/file/{n}") for n in range(5)]
    results = []
    for mode in MODES:
        out = tmp_path / mode
        run_mode(mode, urls, out)
        results.append(file_contents(out))
    assert results[0] == results[1] == results[2]


@pytest.mark.parametrize("mode", ["threads", "async"])
def test_concurrency_is_limited_but_real(server, tmp_path, mode):
    urls = [server.url(f"/slow/{n}") for n in range(8)]
    start = time.perf_counter()
    run_mode(mode, urls, tmp_path, workers=4)
    elapsed = time.perf_counter() - start
    assert server.max_active <= 4, f"{server.max_active} downloads ran at once; the limit was 4"
    assert server.max_active >= 2, "Downloads don't seem to overlap at all"
    assert elapsed < 8 * 0.3, f"8 slow downloads with 4 workers took {elapsed:.2f}s; that's no faster than sequential"


def test_progress_counter_is_correct_with_32_threads(server, tmp_path, capsys):
    urls = [server.url(f"/file/{n}") for n in range(40)]
    download.download_threaded(urls, tmp_path, 32)
    counters = re.findall(r"\[(\d+)/40\]", capsys.readouterr().out)
    assert sorted(map(int, counters)) == list(range(1, 41))


class TestTimed:
    def test_keeps_name_and_result(self, capsys):
        @download.timed
        def add(a, b):
            return a + b

        assert add(2, 3) == 5
        assert add.__name__ == "add"
        output = capsys.readouterr().out
        assert "add" in output and "took" in output


class TestCommandLine:
    def run(self, *args, cwd):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        return subprocess.run(
            [sys.executable, str(DOWNLOAD), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", timeout=60, cwd=cwd, env=env,
        )

    def test_threads_mode(self, server, tmp_path):
        urls = [server.url(f"/file/{n}") for n in range(4)]
        (tmp_path / "urls.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")
        result = self.run("urls.txt", "--out", "downloads", "--mode", "threads", "--workers", "4", cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert len(file_contents(tmp_path / "downloads")) == 4

    def test_failures_give_exit_code_1(self, server, tmp_path):
        urls = [server.url("/file/1"), server.url("/missing")]
        (tmp_path / "urls.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")
        result = self.run("urls.txt", "--out", "downloads", "--mode", "async", cwd=tmp_path)
        assert result.returncode == 1
        assert "Traceback" not in result.stderr
