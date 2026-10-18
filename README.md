# Python Through Projects

A sequence of 12 projects. Each one introduces a few new concepts and reuses what came before, so do them in order.

| # | Project | New concepts |
|---|---------|--------------|
| 01 | [Tip Calculator](01-tip-calculator/README.md) | `print`, `input`, variables, types, arithmetic, f-strings, `if` |
| 02 | [Number Guessing Game](02-number-guessing-game/README.md) | `while`/`for` loops, `random`, `break`/`continue`, basic `try`/`except` |
| 03 | [Text Analyzer](03-text-analyzer/README.md) | functions, strings, lists, dicts, reading files |
| 04 | [Todo List CLI](04-todo-cli/README.md) | lists of dicts, menu loops, JSON persistence, `pathlib` |
| 05 | [Gradebook](05-gradebook/README.md) | modules, comprehensions, sorting with `key=`, CSV |
| 06 | [Bank Accounts](06-bank-accounts/README.md) | classes, inheritance, properties, custom exceptions, dunder methods |
| 07 | [Library Manager](07-library-manager/README.md) | dataclasses, enums, type hints, composition, unit tests |
| 08 | [Log Analyzer](08-log-analyzer/README.md) | `argparse`, regex, generators, `datetime`, `collections` |
| 09 | [Weather CLI](09-weather-cli/README.md) | HTTP APIs, virtual environments, `pip`, caching, error handling |
| 10 | [Expense Tracker](10-expense-tracker/README.md) | `sqlite3`, packages, subcommands, `pytest` |
| 11 | [Concurrent Downloader](11-concurrent-downloader/README.md) | threads, `concurrent.futures`, `asyncio` |
| 12 | [Capstone: Expense API](12-capstone-expense-api/README.md) | web APIs with FastAPI, layered architecture, integration tests |

## How to work through a project

1. Read the whole spec before you write any code.
2. Write your code inside that project's folder (start with `main.py` unless the spec says otherwise).
3. Get the **Core requirements** working first. Check every box under **Done when**.
4. Run the automated checks (see below) until they all pass.
5. Try at least one **Stretch goal**. They're where most of the learning happens.
6. Look back at your code before moving on: is anything repeated that could be a function? Is anything confusingly named?

Rules of thumb:
- Run your code often. Write a few lines, run, repeat.
- When you're stuck, read the error message from the bottom up. The last line tells you *what* went wrong; the lines above tell you *where*.
- Use the [official docs](https://docs.python.org/3/) for anything listed under **Concepts**.
- Try not to copy finished solutions. Look up individual concepts instead.

## Setup

Python 3.14 is installed. Run a project with:

```powershell
cd 01-tip-calculator
python main.py
```

From project 09 onward you'll install third-party packages. That spec explains virtual environments.

## Checking your work

Every project has a `spec_tests/` folder containing automated checks written against the spec. Each spec ends with an **Automated checks** section listing the exact file, function, and class names the checks expect, so read that before you start coding.

Install the test runner once:

```powershell
python -m pip install pytest
```

Then, from inside a project folder:

```powershell
cd 03-text-analyzer
python -m pytest spec_tests -v
```

- Run the checks often, not just at the end. A failing check tells you which requirement isn't met yet. Read its name and the assertion message.
- Don't edit the files in `spec_tests/`. When a project asks you to write your own tests, put them in a separate `tests/` folder. `python -m pytest` (with no folder) runs both.
- The checks cover the **Core requirements**. Stretch goals are up to you, but make sure the checks still pass afterwards.
- Run checks from inside the project folder (`python -m pytest`, not plain `pytest`), so Python can find your modules.
