"""Checks for project 04. Run from the project folder: python -m pytest spec_tests -v"""

import ast
import inspect
import json

import pytest

import main as todo


@pytest.fixture
def tasks():
    tasks = []
    todo.add_task(tasks, "Buy milk", "low")
    todo.add_task(tasks, "Write project 04", "high")
    todo.add_task(tasks, "Call mom", "medium")
    return tasks


@pytest.fixture
def scripted_input(monkeypatch):
    def _script(*answers):
        answers = list(answers)

        def fake_input(prompt=""):
            if not answers:
                pytest.fail("main() asked for more input than expected. Does '6' quit?")
            return answers.pop(0)

        monkeypatch.setattr("builtins.input", fake_input)

    return _script


class TestAddTask:
    def test_returns_and_appends_the_new_task(self):
        tasks = []
        task = todo.add_task(tasks, "Buy milk", "high")
        assert task == {"id": 1, "title": "Buy milk", "done": False, "priority": "high"}
        assert tasks == [task]

    def test_priority_defaults_to_medium(self):
        task = todo.add_task([], "Buy milk")
        assert task["priority"] == "medium"

    def test_title_is_stripped_and_priority_lowercased(self):
        task = todo.add_task([], "   Buy milk  ", "HIGH")
        assert task["title"] == "Buy milk"
        assert task["priority"] == "high"

    def test_ids_increase(self, tasks):
        assert [t["id"] for t in tasks] == [1, 2, 3]

    def test_no_duplicate_id_after_delete(self, tasks):
        todo.delete_task(tasks, 2)
        task = todo.add_task(tasks, "New task")
        assert task["id"] == 4

    @pytest.mark.parametrize("title", ["", "   "])
    def test_empty_title_is_rejected(self, title):
        with pytest.raises(ValueError):
            todo.add_task([], title)

    def test_unknown_priority_is_rejected(self):
        with pytest.raises(ValueError):
            todo.add_task([], "Buy milk", "urgent")


class TestChangingTasks:
    def test_find_task(self, tasks):
        assert todo.find_task(tasks, 2)["title"] == "Write project 04"
        assert todo.find_task(tasks, 99) is None

    def test_complete_task(self, tasks):
        task = todo.complete_task(tasks, 1)
        assert task["done"] is True
        assert todo.find_task(tasks, 1)["done"] is True

    def test_complete_unknown_task(self, tasks):
        assert todo.complete_task(tasks, 99) is None
        assert not any(t["done"] for t in tasks)

    def test_delete_task(self, tasks):
        removed = todo.delete_task(tasks, 2)
        assert removed["title"] == "Write project 04"
        assert [t["id"] for t in tasks] == [1, 3]

    def test_delete_unknown_task(self, tasks):
        assert todo.delete_task(tasks, 99) is None
        assert len(tasks) == 3

    def test_edit_task(self, tasks):
        task = todo.edit_task(tasks, 3, "Call dad")
        assert task["title"] == "Call dad"
        assert todo.find_task(tasks, 3)["title"] == "Call dad"

    def test_edit_unknown_task(self, tasks):
        assert todo.edit_task(tasks, 99, "Anything") is None

    def test_edit_rejects_empty_title(self, tasks):
        with pytest.raises(ValueError):
            todo.edit_task(tasks, 1, "  ")

    @pytest.mark.parametrize(
        "name", ["add_task", "find_task", "complete_task", "delete_task", "edit_task"]
    )
    def test_logic_functions_do_not_print_or_ask(self, name):
        tree = ast.parse(inspect.getsource(getattr(todo, name)))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert not calls & {"print", "input"}, f"{name} should not call print() or input()"


class TestStorage:
    def test_round_trip(self, tasks, tmp_path):
        path = tmp_path / "tasks.json"
        todo.complete_task(tasks, 1)
        todo.save_tasks(path, tasks)
        assert todo.load_tasks(path) == tasks

    def test_file_is_plain_json(self, tasks, tmp_path):
        path = tmp_path / "tasks.json"
        todo.save_tasks(path, tasks)
        assert json.loads(path.read_text(encoding="utf-8")) == tasks

    def test_missing_file_gives_empty_list(self, tmp_path):
        assert todo.load_tasks(tmp_path / "nope.json") == []

    def test_corrupted_file_gives_empty_list(self, tmp_path):
        path = tmp_path / "tasks.json"
        path.write_text("{ this is not json", encoding="utf-8")
        assert todo.load_tasks(path) == []


class TestPrintTasks:
    def test_empty(self, capsys):
        todo.print_tasks([])
        assert "No tasks yet." in capsys.readouterr().out

    def test_shows_status_id_priority_and_title(self, tasks, capsys):
        todo.complete_task(tasks, 1)
        todo.print_tasks(tasks)
        output = capsys.readouterr().out
        assert "[x]" in output and "[ ]" in output
        for expected in ["#1", "#2", "#3", "Buy milk", "high", "low"]:
            assert expected in output


class TestMain:
    def test_changes_survive_a_restart(self, tmp_path, scripted_input, capsys):
        path = tmp_path / "tasks.json"
        scripted_input("2", "Write tests", "high", "3", "1", "6")
        todo.main(path)
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert saved == [{"id": 1, "title": "Write tests", "done": True, "priority": "high"}]

        capsys.readouterr()
        scripted_input("1", "6")
        todo.main(path)
        assert "Write tests" in capsys.readouterr().out

    def test_blank_priority_means_medium(self, tmp_path, scripted_input):
        path = tmp_path / "tasks.json"
        scripted_input("2", "Something", "", "6")
        todo.main(path)
        assert json.loads(path.read_text(encoding="utf-8"))[0]["priority"] == "medium"

    def test_edit_and_delete_from_the_menu(self, tmp_path, scripted_input):
        path = tmp_path / "tasks.json"
        scripted_input("2", "First", "", "2", "Second", "", "5", "1", "Renamed", "4", "2", "6")
        todo.main(path)
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert [(t["id"], t["title"]) for t in saved] == [(1, "Renamed")]

    def test_bad_choices_and_ids_do_not_crash(self, tmp_path, scripted_input):
        path = tmp_path / "tasks.json"
        scripted_input("9", "abc", "3", "42", "3", "abc", "4", "7", "6")
        todo.main(path)
