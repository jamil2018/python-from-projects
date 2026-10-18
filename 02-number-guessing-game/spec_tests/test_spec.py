"""Checks for project 02. Run from the project folder: python -m pytest spec_tests -v"""

import random
import re
import runpy
from pathlib import Path

import pytest

MAIN = Path(__file__).resolve().parent.parent / "main.py"


class OutOfInput(BaseException):
    """Raised when the program asks for more input than the test typed."""


@pytest.fixture
def play(monkeypatch, capsys):
    """Run main.py with scripted answers and a fixed sequence of secret numbers.

    Returns (output, randint_calls).
    """

    def _play(answers, secrets):
        if not MAIN.exists():
            pytest.fail(f"Create {MAIN.name} in {MAIN.parent} first.")
        answers = list(answers)
        secrets = list(secrets)
        randint_calls = []

        def fake_input(prompt=""):
            print(prompt, end="")
            if not answers:
                raise OutOfInput
            answer = answers.pop(0)
            print(answer)
            return answer

        def fake_randint(a, b):
            randint_calls.append((a, b))
            if not secrets:
                raise OutOfInput
            return secrets.pop(0)

        monkeypatch.setattr("builtins.input", fake_input)
        monkeypatch.setattr(random, "randint", fake_randint)
        try:
            runpy.run_path(str(MAIN), run_name="__main__")
        except OutOfInput:
            output = capsys.readouterr().out
            pytest.fail(
                "The program kept asking for input after the test ran out of answers. "
                "Does it stop after answering 'n' to 'Play again?', and does it use "
                f"random.randint(1, 100)?\n--- output ---\n{output}"
            )
        except SystemExit:
            pass
        return capsys.readouterr().out, randint_calls

    return _play


def attempts_reported(output):
    return [int(n) for n in re.findall(r"(\d+)\s+attempts?\b", output, flags=re.IGNORECASE)]


def test_secret_is_between_1_and_100(play):
    _, calls = play(["50", "n"], secrets=[50])
    assert calls == [(1, 100)]


def test_hints_and_attempt_count(play):
    output, _ = play(["50", "25", "37", "n"], secrets=[37])
    lowered = output.lower()
    assert "too high" in lowered
    assert "too low" in lowered
    assert "correct" in lowered
    assert 3 in attempts_reported(output), f"Expected '3 attempts' in the output:\n{output}"


def test_non_numeric_input_is_not_an_attempt(play):
    output, _ = play(["banana", "", "12.5", "37", "n"], secrets=[37])
    assert 1 in attempts_reported(output), (
        f"Invalid input shouldn't count as an attempt. Expected '1 attempt':\n{output}"
    )


def test_out_of_range_guess_is_not_an_attempt(play):
    output, _ = play(["0", "101", "-5", "37", "n"], secrets=[37])
    assert 1 in attempts_reported(output), (
        f"Guesses outside 1-100 shouldn't count. Expected '1 attempt':\n{output}"
    )


def test_play_again_starts_a_fresh_game(play):
    output, calls = play(["10", "y", "90", "20", "n"], secrets=[10, 20])
    assert len(calls) == 2, "Each new game should pick a new secret with random.randint"
    assert output.lower().count("correct") == 2
    reported = attempts_reported(output)
    assert 1 in reported and 2 in reported, (
        f"Expected '1 attempt' for game one and '2 attempts' for game two:\n{output}"
    )
