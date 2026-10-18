"""Checks for project 03. Run from the project folder: python -m pytest spec_tests -v"""

import inspect

import pytest

import main as analyzer


class TestLoadText:
    def test_returns_file_contents(self, tmp_path):
        path = tmp_path / "sample.txt"
        path.write_text("Hello there.\nGeneral Kenobi!", encoding="utf-8")
        assert analyzer.load_text(path) == "Hello there.\nGeneral Kenobi!"

    def test_accepts_a_string_path(self, tmp_path):
        path = tmp_path / "sample.txt"
        path.write_text("abc", encoding="utf-8")
        assert analyzer.load_text(str(path)) == "abc"


class TestCleanWords:
    def test_lowercases_and_strips_punctuation(self):
        assert analyzer.clean_words('"Hello," she said. HELLO!') == ["hello", "she", "said", "hello"]

    def test_handles_all_kinds_of_whitespace(self):
        assert analyzer.clean_words("  one\ttwo\n\nthree  ") == ["one", "two", "three"]

    def test_never_returns_empty_strings(self):
        assert analyzer.clean_words("wait - what ... ?!") == ["wait", "what"]

    def test_empty_text(self):
        assert analyzer.clean_words("") == []


class TestCounting:
    def test_count_words(self):
        assert analyzer.count_words(["a", "b", "a"]) == 3
        assert analyzer.count_words([]) == 0

    def test_count_unique(self):
        assert analyzer.count_unique(["a", "b", "a"]) == 2
        assert analyzer.count_unique([]) == 0

    def test_word_frequencies(self):
        assert analyzer.word_frequencies(["the", "cat", "the", "mat", "the"]) == {
            "the": 3,
            "cat": 1,
            "mat": 1,
        }

    def test_word_frequencies_of_nothing(self):
        assert analyzer.word_frequencies([]) == {}

    def test_word_frequencies_is_built_by_hand(self):
        source = inspect.getsource(analyzer.word_frequencies)
        assert "Counter" not in source, "Build the dict yourself; Counter comes in project 08."


class TestTopN:
    def test_most_common_first_with_alphabetical_ties(self):
        freqs = {"the": 5, "sat": 3, "cat": 3, "mat": 1}
        assert analyzer.top_n(freqs, 3) == [("the", 5), ("cat", 3), ("sat", 3)]

    def test_default_is_ten(self):
        freqs = {f"word{chr(97 + i)}": i + 1 for i in range(12)}
        assert len(analyzer.top_n(freqs)) == 10

    def test_n_larger_than_vocabulary(self):
        assert analyzer.top_n({"a": 1, "b": 2}, 10) == [("b", 2), ("a", 1)]


class TestLengths:
    def test_average_word_length(self):
        assert analyzer.average_word_length(["a", "abc"]) == pytest.approx(2.0)
        assert analyzer.average_word_length(["hello", "hi", "hey"]) == pytest.approx(10 / 3)

    def test_average_word_length_of_nothing(self):
        assert analyzer.average_word_length([]) == 0.0

    def test_longest_words_are_distinct_and_longest_first(self):
        words = ["hi", "extraordinary", "hi", "responsibility", "cat", "extraordinary"]
        assert analyzer.longest_words(words, 2) == ["responsibility", "extraordinary"]

    def test_longest_words_ties_are_alphabetical(self):
        assert analyzer.longest_words(["bbb", "aaa", "c", "ccc"], 2) == ["aaa", "bbb"]

    def test_longest_words_default_is_five(self):
        words = ["a" * i for i in range(1, 9)]
        assert len(analyzer.longest_words(words)) == 5


class TestMain:
    def test_report_and_missing_file(self, tmp_path, monkeypatch, capsys):
        path = tmp_path / "sample.txt"
        path.write_text("apple " * 1000 + "Banana, " * 234, encoding="utf-8")
        answers = [str(tmp_path / "does-not-exist.txt"), str(path)]

        def fake_input(prompt=""):
            if not answers:
                pytest.fail("main() asked for more input than expected")
            return answers.pop(0)

        monkeypatch.setattr("builtins.input", fake_input)
        analyzer.main()
        output = capsys.readouterr().out
        assert "1,234" in output, "Total words should be printed with a thousands separator"
        assert "apple" in output and "banana" in output
