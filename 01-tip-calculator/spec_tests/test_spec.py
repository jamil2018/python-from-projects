"""Checks for project 01. Run from the project folder: python -m pytest spec_tests -v"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

MAIN = Path(__file__).resolve().parent.parent / "main.py"


def run(*answers):
    """Run main.py, typing each answer followed by Enter."""
    if not MAIN.exists():
        pytest.fail(f"Create {MAIN.name} in {MAIN.parent} first.")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    try:
        result = subprocess.run(
            [sys.executable, str(MAIN)],
            input="\n".join(answers) + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            cwd=MAIN.parent,
            env=env,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("main.py didn't finish within 10 seconds. Is it waiting for more input?")
    return result


def assert_no_crash(result):
    assert result.returncode == 0 and "Traceback" not in result.stderr, (
        f"main.py crashed:\n{result.stderr}"
    )


def test_example_from_spec():
    result = run("84.50", "20", "3")
    assert_no_crash(result)
    for expected in ["16.90", "101.40", "33.80"]:
        assert expected in result.stdout, f"Expected {expected} in the output:\n{result.stdout}"


@pytest.mark.parametrize(
    "bill, tip, people, expected",
    [
        ("100", "15", "4", ["15.00", "115.00", "28.75"]),
        ("50", "18", "3", ["9.00", "59.00", "19.67"]),
        ("10", "0", "1", ["0.00", "10.00"]),
        ("1234.56", "10", "2", ["123.46", "1358.02", "679.01"]),
    ],
)
def test_calculations(bill, tip, people, expected):
    result = run(bill, tip, people)
    assert_no_crash(result)
    for value in expected:
        assert value in result.stdout.replace(",", ""), (
            f"bill={bill}, tip={tip}%, people={people}: expected {value} in the output:\n{result.stdout}"
        )


def test_money_has_exactly_two_decimals():
    result = run("100", "10", "2")
    assert_no_crash(result)
    one_decimal = re.findall(r"\d+\.\d(?!\d)", result.stdout)
    assert not one_decimal, f"These numbers need 2 decimal places: {one_decimal}"


@pytest.mark.parametrize("people", ["0", "-2"])
def test_invalid_number_of_people_does_not_crash(people):
    result = run("100", "15", people)
    assert_no_crash(result)
    assert "ZeroDivisionError" not in result.stdout + result.stderr
