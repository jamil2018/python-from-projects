# 10 · Expense Tracker

A personal expense tracker backed by a **SQLite database**, organized as a proper Python package with a test suite. The capstone (project 12) builds on this code, so design it carefully.

**Builds on:** 04 (CRUD app), 05 (CSV), 07 (dataclasses + tests), 08 (argparse), 09 (packages + venv).

## Concepts
- `sqlite3`: connections, cursors, `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`
- Parameterized queries (`?` placeholders) and why string formatting SQL is dangerous (SQL injection)
- Transactions and context managers (`with conn:`)
- The repository pattern: hiding SQL behind a class
- `argparse` subcommands (`add_subparsers`)
- `pytest`: fixtures, `tmp_path`, `pytest.raises`, parametrize
- `pyproject.toml` and installing your own package with `pip install -e .`

## Project layout
```
10-expense-tracker/
  pyproject.toml
  src/expenses/
    __init__.py
    models.py        # Expense, Category dataclasses
    repository.py    # ExpenseRepository: all SQL lives here
    service.py       # business rules (budgets, summaries)
    cli.py           # argparse subcommands
  tests/
    conftest.py      # fixture: repository using a temp database
    test_repository.py
    test_service.py
```

## Database schema
```sql
categories(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, monthly_budget REAL)
expenses(id INTEGER PRIMARY KEY, amount REAL NOT NULL, category_id INTEGER REFERENCES categories(id),
         description TEXT, spent_on TEXT NOT NULL)  -- ISO date
```

## Core requirements
```
expenses add 12.50 food "Lunch" --date 2026-10-18
expenses list [--month 2026-10] [--category food]
expenses edit 7 --amount 15
expenses delete 7
expenses categories add food --budget 300
expenses summary --month 2026-10
expenses import bank.csv
expenses export --month 2026-10 out.csv
```
1. Every query uses `?` placeholders. No f-strings in SQL.
2. `summary` shows the total per category, the budget, the remaining amount, and a warning when a category is over budget.
3. `import` reads a CSV and inserts every row in **one transaction**. If any row is invalid, nothing is imported.
4. The database path defaults to `~/.expenses.db` and can be overridden with `--db` (tests use a temporary path).
5. After `pip install -e .`, an `expenses` command works from any directory (configure `[project.scripts]` in `pyproject.toml`).

## Tests
```powershell
pip install pytest
pytest -v
```
- Use a fixture that gives each test a fresh database in `tmp_path`.
- Use `@pytest.mark.parametrize` for input validation cases.
- Test that a bad CSV row rolls back the whole import.
- Aim for 20+ tests.

## Done when
- [ ] `cli.py` never touches SQL, and `repository.py` never prints
- [ ] Running `expenses add 5 food "x'; DROP TABLE expenses; --"` stores that text harmlessly
- [ ] All tests pass and none of them touch your real database

## Stretch goals
- Recurring expenses (monthly rent) that are automatically added each month.
- Track the schema version and write a migration that adds a `payment_method` column.
- Make `list` output prettier with the [`rich`](https://github.com/Textualize/rich) library.

## Automated checks
Your own tests go in `tests/`. The provided checks in `spec_tests/` import from `src/expenses/` and assume the following.

`models.py`:
- `Category(id, name, monthly_budget)`, where `monthly_budget` may be `None`.
- `Expense(id, amount, category, description, spent_on)`. `category` is the category's *name*, and `spent_on` is a `datetime.date`.

`repository.py`: `ExpenseRepository(db_path)` creates the tables if they're missing, and provides:
- `add_category(name, monthly_budget=None) -> Category`. A duplicate name raises `ValueError`.
- `get_category(name)` and `list_categories()`, sorted by name.
- `add_expense(amount, category, description, spent_on) -> Expense`. An unknown category is created automatically, without a budget.
- `get_expense(id)`, which returns `None` when the id doesn't exist.
- `list_expenses(month=None, category=None)`, ordered by date and then id. `month` is `"YYYY-MM"`.
- `update_expense(id, amount=None, category=None, description=None, spent_on=None)`. Only the fields you pass change. Returns the updated `Expense`, or `None` if the id doesn't exist.
- `delete_expense(id) -> bool`
- `totals_by_category(month) -> dict[str, float]`
- `add_many(rows)`, which inserts a list of `(amount, category, description, spent_on)` tuples in one transaction.
- `close()`

`service.py`:
- `parse_amount(text) -> float` and `parse_month(text) -> str` raise `ValueError` on bad input. Amounts must be positive.
- `monthly_summary(repo, month)` returns a list of objects with the attributes `category`, `spent`, `budget`, `remaining`, and `over_budget`. It's sorted by category and covers every category that has spending that month or has a budget. `remaining` is `None` when there's no budget.
- `import_csv(repo, path) -> int` imports rows with the columns `date,amount,category,description`. One bad row raises `ValueError`, and then nothing is imported.
- `export_csv(repo, path, month=None) -> int` writes the same columns and returns the number of rows.

`cli.py`:
- `main(argv=None) -> int` returns the exit code. `--db PATH` comes before the subcommand, for example `expenses --db test.db list`.
- `list` and `summary` print amounts with 2 decimals.
- `summary` prints `OVER BUDGET` next to any category that's over.
- Errors such as a bad amount or an unknown id print a message to stderr and return `1`.

`pyproject.toml`: `[project.scripts]` maps `expenses` to `expenses.cli:main`.

```powershell
python -m pytest spec_tests -v
```

## Reflect
If you replaced SQLite with PostgreSQL, which files would have to change? Ideally only `repository.py`. That separation is what makes project 12 possible.
