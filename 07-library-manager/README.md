# 07 · Library Manager

A library system with books, members, and loans, built with modern Python features and backed by **automated tests**.

**Builds on 06:** classes, exceptions, JSON persistence.

## Concepts
- `@dataclass` (including `field(default_factory=...)` and `frozen=True`)
- `enum.Enum`
- Type hints: `list[Book]`, `str | None`, return types
- Composition: objects that hold other objects
- `datetime.date` and `timedelta`
- Unit testing with `unittest` (built in) and `assert`
- Arrange / Act / Assert test structure

## Project layout
```
07-library-manager/
  models.py        # Book, Member, Loan dataclasses, Genre enum
  library.py       # Library service: all business rules
  storage.py       # save/load to library.json
  main.py          # CLI menu
  tests/
    test_library.py
```

## Data model
```python
class Genre(Enum): FICTION, SCIENCE, HISTORY, ...

@dataclass
class Book:     isbn, title, author, genre, copies_total, copies_available

@dataclass
class Member:   member_id, name, max_loans=3

@dataclass
class Loan:     book_isbn, member_id, borrowed_on, due_on, returned_on: date | None = None
```

## Core requirements
`Library` methods:
1. `add_book(...)`: adding an existing ISBN increases its copy count instead of creating a duplicate.
2. `register_member(name)` returns a new `Member`.
3. `checkout(isbn, member_id, today)`:
   - fails if no copies are available, the member is at their loan limit, or the member has any overdue loans
   - the due date is 14 days after `today`
4. `return_book(isbn, member_id, today)` returns the late fee: $0.50 per day overdue.
5. `search(query)` does a case-insensitive match on title or author.
6. `overdue_loans(today)` returns the loans past their due date.
7. `member_history(member_id)` returns all loans for a member, newest first.

Pass `today` in as a parameter instead of calling `date.today()` inside the logic, so tests can control time.

`storage.py` saves and loads the whole library to JSON. Dates are stored as ISO strings and enums by name.

## Tests
Write **at least 12 tests** in `tests/test_library.py`, including:
- a successful checkout reduces `copies_available`
- checkout fails when no copies are left
- checkout fails at the loan limit
- checkout is blocked when the member has an overdue book
- returning 3 days late costs $1.50
- returning on time costs $0
- save then load produces an equal library

Run them with:
```powershell
python -m unittest discover tests
```

## Done when
- [ ] All models are dataclasses with type hints
- [ ] No business rules live in `main.py`
- [ ] At least 12 passing tests
- [ ] Every function signature has type hints

## Stretch goals
- Reservations: a member can reserve a book that's checked out, and the queue is first-come, first-served.
- Install `mypy` (`pip install mypy`) and run `mypy .` until it reports no errors.
- Rewrite the tests in `pytest` style (you'll use pytest from project 10 onward).

## Automated checks
Your own tests go in `tests/`. The provided checks in `spec_tests/` import `models.py`, `library.py`, and `storage.py`. They assume:
- `Genre` has at least `FICTION`, `SCIENCE`, and `HISTORY`.
- `Library` is a dataclass too, with the fields `books: dict[str, Book]` (keyed by ISBN), `members: dict[int, Member]`, and `loans: list[Loan]`. All three default to empty, so `Library()` works. Being a dataclass gives you `==` for free, which makes the save/load test possible.
- `add_book(isbn, title, author, genre, copies=1)` returns the `Book`.
- Member ids are integers, starting at 1.
- Every rule violation raises `LibraryError`, defined in `library.py`. That covers no copies left, the loan limit, overdue loans, an unknown ISBN or member, and returning a book that isn't on loan.
- `return_book` returns the fee as a `Decimal`, for example `Decimal("1.50")`.
- `storage.py` provides `save_library(library, path)` and `load_library(path)`.

These checks are pytest-style, so run them with pytest. Your own `unittest` tests also run under pytest:

```powershell
python -m pip install pytest
python -m pytest -v
```

## Reflect
How did writing tests change the way you designed `Library`? Notice how much easier the functions that take `today` as a parameter were to test.
