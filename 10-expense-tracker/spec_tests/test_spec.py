"""Checks for project 10. Run from the project folder: python -m pytest spec_tests -v"""

import ast
import csv
import inspect
import sqlite3
import tomllib
from datetime import date
from pathlib import Path

import pytest

from expenses import cli, repository, service
from expenses.models import Category, Expense
from expenses.repository import ExpenseRepository

PROJECT_DIR = Path(__file__).resolve().parent.parent
INJECTION = "x'; DROP TABLE expenses; --"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def repo(db_path):
    repo = ExpenseRepository(db_path)
    yield repo
    repo.close()


@pytest.fixture
def october(repo):
    """Categories and expenses used by the summary checks."""
    repo.add_category("food", 300)
    repo.add_category("rent", 1000)
    repo.add_category("travel", 200)
    repo.add_expense(250, "food", "Groceries", date(2026, 10, 3))
    repo.add_expense(80, "food", "Restaurant", date(2026, 10, 20))
    repo.add_expense(1000, "rent", "October rent", date(2026, 10, 1))
    repo.add_expense(20, "fun", "Cinema", date(2026, 10, 11))
    repo.add_expense(500, "food", "Big September shop", date(2026, 9, 28))
    return repo


def cli_run(db_path, *args):
    return cli.main(["--db", str(db_path), *map(str, args)])


class TestRepository:
    def test_creates_tables(self, repo, db_path):
        with sqlite3.connect(db_path) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"categories", "expenses"} <= tables

    def test_add_and_get_category(self, repo):
        category = repo.add_category("food", 300)
        assert isinstance(category, Category)
        assert isinstance(category.id, int)
        assert (category.name, category.monthly_budget) == ("food", 300)
        assert repo.get_category("food") == category
        assert repo.get_category("nope") is None

    def test_duplicate_category(self, repo):
        repo.add_category("food")
        with pytest.raises(ValueError):
            repo.add_category("food")

    def test_list_categories_sorted(self, repo):
        for name in ["rent", "food", "travel"]:
            repo.add_category(name)
        assert [c.name for c in repo.list_categories()] == ["food", "rent", "travel"]

    def test_add_and_get_expense(self, repo):
        expense = repo.add_expense(12.5, "food", "Lunch", date(2026, 10, 18))
        assert isinstance(expense, Expense)
        assert isinstance(expense.id, int)
        assert (expense.amount, expense.category, expense.description, expense.spent_on) == (
            12.5, "food", "Lunch", date(2026, 10, 18),
        )
        assert repo.get_expense(expense.id) == expense
        assert repo.get_expense(9999) is None

    def test_unknown_category_is_created(self, repo):
        repo.add_expense(5, "snacks", "Chips", date(2026, 10, 18))
        category = repo.get_category("snacks")
        assert category is not None and category.monthly_budget is None

    def test_list_expenses_filters_and_order(self, october):
        assert [e.description for e in october.list_expenses(month="2026-10")] == [
            "October rent", "Groceries", "Cinema", "Restaurant",
        ]
        assert [e.description for e in october.list_expenses(category="food")] == [
            "Big September shop", "Groceries", "Restaurant",
        ]
        assert [e.description for e in october.list_expenses(month="2026-09", category="food")] == [
            "Big September shop",
        ]
        assert len(october.list_expenses()) == 5

    def test_update_expense(self, repo):
        expense = repo.add_expense(12.5, "food", "Lunch", date(2026, 10, 18))
        updated = repo.update_expense(expense.id, amount=15)
        assert updated.amount == 15
        assert updated.description == "Lunch"
        assert repo.get_expense(expense.id).amount == 15

    def test_update_category_and_date(self, repo):
        expense = repo.add_expense(12.5, "food", "Lunch", date(2026, 10, 18))
        repo.update_expense(expense.id, category="work", spent_on=date(2026, 10, 17))
        stored = repo.get_expense(expense.id)
        assert (stored.category, stored.spent_on) == ("work", date(2026, 10, 17))

    def test_update_missing(self, repo):
        assert repo.update_expense(9999, amount=1) is None

    def test_delete_expense(self, repo):
        expense = repo.add_expense(12.5, "food", "Lunch", date(2026, 10, 18))
        assert repo.delete_expense(expense.id) is True
        assert repo.get_expense(expense.id) is None
        assert repo.delete_expense(expense.id) is False

    def test_totals_by_category(self, october):
        assert october.totals_by_category("2026-10") == {"food": 330, "fun": 20, "rent": 1000}

    def test_sql_injection_is_harmless(self, repo):
        expense = repo.add_expense(5, "food", INJECTION, date(2026, 10, 18))
        assert repo.get_expense(expense.id).description == INJECTION
        assert repo.list_expenses(category="food' OR '1'='1") == []
        assert len(repo.list_expenses()) == 1

    def test_data_persists(self, db_path):
        first = ExpenseRepository(db_path)
        first.add_expense(5, "food", "Snack", date(2026, 10, 18))
        first.close()
        second = ExpenseRepository(db_path)
        assert [e.description for e in second.list_expenses()] == ["Snack"]
        second.close()

    def test_add_many(self, repo):
        repo.add_many([
            (1, "food", "a", date(2026, 10, 1)),
            (2, "rent", "b", date(2026, 10, 2)),
        ])
        assert [e.amount for e in repo.list_expenses()] == [1, 2]


class TestService:
    @pytest.mark.parametrize("text, expected", [("12.50", 12.5), ("3", 3.0), (" 7.25 ", 7.25)])
    def test_parse_amount(self, text, expected):
        assert service.parse_amount(text) == pytest.approx(expected)

    @pytest.mark.parametrize("text", ["abc", "0", "-5", "", "1,000"])
    def test_parse_amount_rejects(self, text):
        with pytest.raises(ValueError):
            service.parse_amount(text)

    def test_parse_month(self):
        assert service.parse_month("2026-10") == "2026-10"

    @pytest.mark.parametrize("text", ["2026-13", "Oct", "2026-1", "26-10", "2026/10", ""])
    def test_parse_month_rejects(self, text):
        with pytest.raises(ValueError):
            service.parse_month(text)

    def test_monthly_summary(self, october):
        rows = {r.category: r for r in service.monthly_summary(october, "2026-10")}
        assert list(rows) == ["food", "fun", "rent", "travel"]

        food = rows["food"]
        assert (food.spent, food.budget, food.remaining, food.over_budget) == (330, 300, -30, True)
        fun = rows["fun"]
        assert (fun.spent, fun.budget, fun.remaining, fun.over_budget) == (20, None, None, False)
        rent = rows["rent"]
        assert (rent.remaining, rent.over_budget) == (0, False)
        travel = rows["travel"]
        assert (travel.spent, travel.remaining, travel.over_budget) == (0, 200, False)

    def test_import_csv(self, repo, tmp_path):
        path = tmp_path / "bank.csv"
        path.write_text(
            "date,amount,category,description\n"
            "2026-10-01,12.50,food,Lunch\n"
            "2026-10-02,40,transport,\"Taxi, airport\"\n"
            "2026-10-03,9.99,food,Snacks\n",
            encoding="utf-8",
        )
        assert service.import_csv(repo, path) == 3
        assert [e.description for e in repo.list_expenses()] == ["Lunch", "Taxi, airport", "Snacks"]

    def test_bad_row_imports_nothing(self, repo, tmp_path):
        path = tmp_path / "bank.csv"
        path.write_text(
            "date,amount,category,description\n"
            "2026-10-01,12.50,food,Lunch\n"
            "2026-10-02,abc,food,Broken\n"
            "2026-10-03,9.99,food,Snacks\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError):
            service.import_csv(repo, path)
        assert repo.list_expenses() == []

    def test_export_csv(self, october, tmp_path):
        path = tmp_path / "out.csv"
        assert service.export_csv(october, path, month="2026-10") == 4
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ["date", "amount", "category", "description"]
            rows = list(reader)
        assert rows[0]["date"] == "2026-10-01" and rows[0]["description"] == "October rent"
        assert float(rows[0]["amount"]) == 1000


class TestCli:
    def test_add_and_list(self, db_path, capsys):
        assert cli_run(db_path, "add", "12.50", "food", "Lunch", "--date", "2026-10-18") == 0
        capsys.readouterr()
        assert cli_run(db_path, "list") == 0
        output = capsys.readouterr().out
        assert "Lunch" in output and "12.50" in output and "2026-10-18" in output

    def test_list_filters(self, db_path, capsys):
        cli_run(db_path, "add", "5", "food", "October snack", "--date", "2026-10-18")
        cli_run(db_path, "add", "7", "rent", "September thing", "--date", "2026-09-18")
        capsys.readouterr()
        cli_run(db_path, "list", "--month", "2026-10")
        output = capsys.readouterr().out
        assert "October snack" in output and "September thing" not in output
        cli_run(db_path, "list", "--category", "rent")
        output = capsys.readouterr().out
        assert "September thing" in output and "October snack" not in output

    def test_edit(self, db_path, capsys):
        cli_run(db_path, "add", "12.50", "food", "Lunch", "--date", "2026-10-18")
        repo = ExpenseRepository(db_path)
        expense_id = repo.list_expenses()[0].id
        repo.close()
        assert cli_run(db_path, "edit", expense_id, "--amount", "15") == 0
        capsys.readouterr()
        cli_run(db_path, "list")
        assert "15.00" in capsys.readouterr().out

    def test_delete(self, db_path):
        cli_run(db_path, "add", "12.50", "food", "Lunch", "--date", "2026-10-18")
        repo = ExpenseRepository(db_path)
        expense_id = repo.list_expenses()[0].id
        repo.close()
        assert cli_run(db_path, "delete", expense_id) == 0
        assert cli_run(db_path, "delete", expense_id) == 1

    def test_summary_warns_when_over_budget(self, db_path, capsys):
        cli_run(db_path, "categories", "add", "food", "--budget", "300")
        cli_run(db_path, "add", "250", "food", "Groceries", "--date", "2026-10-03")
        cli_run(db_path, "add", "80", "food", "Restaurant", "--date", "2026-10-20")
        capsys.readouterr()
        assert cli_run(db_path, "summary", "--month", "2026-10") == 0
        output = capsys.readouterr().out
        assert "330.00" in output and "300.00" in output
        assert "OVER BUDGET" in output

    def test_bad_amount(self, db_path, capsys):
        assert cli_run(db_path, "add", "abc", "food", "Lunch") == 1
        assert capsys.readouterr().err.strip(), "Explain the error on stderr"

    def test_injection_through_the_cli(self, db_path, capsys):
        cli_run(db_path, "add", "5", "food", INJECTION, "--date", "2026-10-18")
        capsys.readouterr()
        assert cli_run(db_path, "list") == 0
        assert INJECTION in capsys.readouterr().out

    def test_import_and_export(self, db_path, tmp_path):
        source = tmp_path / "bank.csv"
        source.write_text(
            "date,amount,category,description\n2026-10-01,12.50,food,Lunch\n",
            encoding="utf-8",
        )
        assert cli_run(db_path, "import", source) == 0
        out = tmp_path / "out.csv"
        assert cli_run(db_path, "export", "--month", "2026-10", out) == 0
        assert "Lunch" in out.read_text(encoding="utf-8")


class TestStructure:
    def test_cli_has_no_sql(self):
        source = inspect.getsource(cli)
        assert "sqlite3" not in source and ".execute(" not in source, "Keep SQL in repository.py"

    def test_repository_never_prints(self):
        tree = ast.parse(inspect.getsource(repository))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "print" not in calls

    def test_console_script(self):
        pyproject = PROJECT_DIR / "pyproject.toml"
        assert pyproject.exists(), "Create pyproject.toml"
        config = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        assert config["project"]["scripts"]["expenses"] == "expenses.cli:main"
