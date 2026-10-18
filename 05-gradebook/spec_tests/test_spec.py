"""Checks for project 05. Run from the project folder: python -m pytest spec_tests -v"""

import ast
import csv
import inspect
import re
import statistics

import pytest

import gradebook

CSV_TEXT = """name,homework,midterm,final
Alice,92,88,95
Bob,75,64,80
Chen,58,71,62
Dana,85,90,88
Eli,40,55,50
Finn,abc,70,70
Gus,80,,90
Hana,100,100,100
"""

# Final scores with the default weights (30/30/40).
EXPECTED_FINALS = {
    "Alice": 92.0,
    "Bob": 73.7,
    "Chen": 63.5,
    "Dana": 87.7,
    "Eli": 48.5,
    "Hana": 100.0,
}


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "grades.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")
    return path


@pytest.fixture
def students(csv_path):
    students, _ = gradebook.load_students(csv_path)
    return students


def by_name(students, name):
    return next(s for s in students if s["name"] == name)


class TestLoadStudents:
    def test_loads_valid_rows(self, students):
        assert [s["name"] for s in students] == ["Alice", "Bob", "Chen", "Dana", "Eli", "Hana"]

    def test_scores_are_numbers(self, students):
        alice = by_name(students, "Alice")
        assert alice["homework"] == 92 and alice["midterm"] == 88 and alice["final"] == 95
        assert all(isinstance(alice[key], (int, float)) for key in ("homework", "midterm", "final"))

    def test_bad_rows_are_reported_with_line_numbers(self, csv_path):
        _, skipped = gradebook.load_students(csv_path)
        assert len(skipped) == 2
        assert re.search(r"\b7\b", skipped[0]), f"Finn is on line 7: {skipped[0]!r}"
        assert re.search(r"\b8\b", skipped[1]), f"Gus is on line 8: {skipped[1]!r}"


class TestScoring:
    def test_weights(self):
        assert gradebook.WEIGHTS == {"homework": 0.3, "midterm": 0.3, "final": 0.4}

    @pytest.mark.parametrize("name, expected", EXPECTED_FINALS.items())
    def test_final_score(self, students, name, expected):
        assert gradebook.final_score(by_name(students, name), gradebook.WEIGHTS) == pytest.approx(expected)

    def test_final_score_uses_the_given_weights(self, students):
        only_final = {"homework": 0, "midterm": 0, "final": 1}
        assert gradebook.final_score(by_name(students, "Alice"), only_final) == pytest.approx(95)

    @pytest.mark.parametrize(
        "score, letter",
        [(100, "A"), (90, "A"), (89.99, "B"), (80, "B"), (79.5, "C"), (70, "C"),
         (69.9, "D"), (60, "D"), (59.99, "F"), (0, "F")],
    )
    def test_letter_grade(self, score, letter):
        assert gradebook.letter_grade(score) == letter


class TestStatistics:
    def test_class_stats(self, students):
        finals = list(EXPECTED_FINALS.values())
        stats = gradebook.class_stats(students)
        assert set(stats) == {"mean", "median", "min", "max", "stdev"}
        assert stats["mean"] == pytest.approx(statistics.mean(finals))
        assert stats["median"] == pytest.approx(statistics.median(finals))
        assert stats["min"] == pytest.approx(48.5)
        assert stats["max"] == pytest.approx(100.0)
        assert stats["stdev"] == pytest.approx(statistics.stdev(finals))

    def test_grade_distribution(self, students):
        assert gradebook.grade_distribution(students) == {"A": 2, "B": 1, "C": 1, "D": 1, "F": 1}

    def test_grade_distribution_includes_zero_counts(self, students):
        top_two = [by_name(students, "Alice"), by_name(students, "Hana")]
        assert gradebook.grade_distribution(top_two) == {"A": 2, "B": 0, "C": 0, "D": 0, "F": 0}

    def test_top_students(self, students):
        top = gradebook.top_students(students, 3)
        assert [s["name"] for s in top] == ["Hana", "Alice", "Dana"]

    def test_top_students_does_not_reorder_the_input(self, students):
        before = [s["name"] for s in students]
        gradebook.top_students(students, 3)
        assert [s["name"] for s in students] == before


class TestExport:
    def test_export_report(self, students, tmp_path):
        path = tmp_path / "report.csv"
        gradebook.export_report(students, path)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ["name", "final", "letter"]
            rows = list(reader)
        assert [r["name"] for r in rows] == ["Hana", "Alice", "Dana", "Bob", "Chen", "Eli"]
        assert rows[3] == {"name": "Bob", "final": "73.70", "letter": "C"}


def test_gradebook_has_no_print_or_input():
    tree = ast.parse(inspect.getsource(gradebook))
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not calls & {"print", "input"}, "gradebook.py must not call print() or input()"
