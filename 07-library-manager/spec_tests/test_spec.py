"""Checks for project 07. Run from the project folder: python -m pytest spec_tests -v"""

import dataclasses
import inspect
import json
from datetime import date, timedelta
from decimal import Decimal

import pytest

import library as library_module
import storage
from library import Library, LibraryError
from models import Book, Genre, Loan, Member

TODAY = date(2026, 10, 1)


@pytest.fixture
def lib():
    lib = Library()
    lib.add_book("111", "Dune", "Frank Herbert", Genre.FICTION)
    lib.add_book("222", "A Brief History of Time", "Stephen Hawking", Genre.SCIENCE, copies=2)
    lib.add_book("333", "SPQR", "Mary Beard", Genre.HISTORY, copies=5)
    lib.add_book("444", "Children of Dune", "Frank Herbert", Genre.FICTION, copies=3)
    return lib


@pytest.fixture
def alice(lib):
    return lib.register_member("Alice")


class TestModels:
    @pytest.mark.parametrize("cls", [Book, Member, Loan, Library])
    def test_are_dataclasses(self, cls):
        assert dataclasses.is_dataclass(cls)

    def test_member_defaults_to_three_loans(self):
        assert Member(1, "Alice").max_loans == 3

    def test_loan_starts_unreturned(self):
        loan = Loan("111", 1, TODAY, TODAY + timedelta(days=14))
        assert loan.returned_on is None

    def test_genre_is_an_enum(self):
        assert {"FICTION", "SCIENCE", "HISTORY"} <= {g.name for g in Genre}


class TestBooksAndMembers:
    def test_add_book(self, lib):
        book = lib.books["222"]
        assert book.title == "A Brief History of Time"
        assert book.copies_total == 2 and book.copies_available == 2

    def test_add_existing_isbn_adds_copies(self, lib):
        book = lib.add_book("111", "Dune", "Frank Herbert", Genre.FICTION, copies=2)
        assert len(lib.books) == 4
        assert book.copies_total == 3 and book.copies_available == 3

    def test_register_member(self, lib):
        a = lib.register_member("Alice")
        b = lib.register_member("Bob")
        assert isinstance(a, Member) and a.name == "Alice"
        assert a.member_id != b.member_id
        assert lib.members[b.member_id] is b

    def test_search_matches_title_or_author_ignoring_case(self, lib):
        assert {b.isbn for b in lib.search("dune")} == {"111", "444"}
        assert {b.isbn for b in lib.search("HAWKING")} == {"222"}
        assert lib.search("nothing like this") == []


class TestCheckout:
    def test_checkout_creates_a_loan_due_in_14_days(self, lib, alice):
        loan = lib.checkout("222", alice.member_id, TODAY)
        assert isinstance(loan, Loan)
        assert loan.book_isbn == "222" and loan.member_id == alice.member_id
        assert loan.borrowed_on == TODAY
        assert loan.due_on == date(2026, 10, 15)
        assert loan in lib.loans

    def test_checkout_reduces_available_copies(self, lib, alice):
        lib.checkout("222", alice.member_id, TODAY)
        assert lib.books["222"].copies_available == 1
        assert lib.books["222"].copies_total == 2

    def test_no_copies_left(self, lib, alice):
        bob = lib.register_member("Bob")
        lib.checkout("111", alice.member_id, TODAY)
        with pytest.raises(LibraryError):
            lib.checkout("111", bob.member_id, TODAY)

    def test_loan_limit(self, lib, alice):
        for _ in range(3):
            lib.checkout("333", alice.member_id, TODAY)
        with pytest.raises(LibraryError):
            lib.checkout("333", alice.member_id, TODAY)
        assert lib.books["333"].copies_available == 2

    def test_overdue_loan_blocks_checkout(self, lib, alice):
        lib.checkout("333", alice.member_id, TODAY)
        with pytest.raises(LibraryError):
            lib.checkout("222", alice.member_id, TODAY + timedelta(days=15))

    def test_loan_due_today_is_not_overdue(self, lib, alice):
        lib.checkout("333", alice.member_id, TODAY)
        lib.checkout("222", alice.member_id, TODAY + timedelta(days=14))

    def test_unknown_book_or_member(self, lib, alice):
        with pytest.raises(LibraryError):
            lib.checkout("999", alice.member_id, TODAY)
        with pytest.raises(LibraryError):
            lib.checkout("111", 999, TODAY)


class TestReturns:
    def test_on_time_return_is_free(self, lib, alice):
        lib.checkout("222", alice.member_id, TODAY)
        fee = lib.return_book("222", alice.member_id, TODAY + timedelta(days=14))
        assert fee == Decimal("0")

    def test_three_days_late_costs_150(self, lib, alice):
        lib.checkout("222", alice.member_id, TODAY)
        fee = lib.return_book("222", alice.member_id, TODAY + timedelta(days=17))
        assert fee == Decimal("1.50")

    def test_return_restores_the_copy_and_closes_the_loan(self, lib, alice):
        loan = lib.checkout("222", alice.member_id, TODAY)
        lib.return_book("222", alice.member_id, TODAY + timedelta(days=3))
        assert lib.books["222"].copies_available == 2
        assert loan.returned_on == TODAY + timedelta(days=3)

    def test_returned_loan_frees_up_the_limit(self, lib, alice):
        for _ in range(3):
            lib.checkout("333", alice.member_id, TODAY)
        lib.return_book("333", alice.member_id, TODAY)
        lib.checkout("333", alice.member_id, TODAY)

    def test_cannot_return_a_book_that_is_not_on_loan(self, lib, alice):
        with pytest.raises(LibraryError):
            lib.return_book("111", alice.member_id, TODAY)


class TestReports:
    def test_overdue_loans(self, lib, alice):
        bob = lib.register_member("Bob")
        late = lib.checkout("333", alice.member_id, TODAY)
        lib.checkout("222", bob.member_id, TODAY + timedelta(days=10))
        returned = lib.checkout("111", bob.member_id, TODAY)
        lib.return_book("111", bob.member_id, TODAY + timedelta(days=1))
        assert lib.overdue_loans(TODAY + timedelta(days=20)) == [late]
        assert returned not in lib.overdue_loans(TODAY + timedelta(days=60))

    def test_member_history_newest_first(self, lib, alice):
        first = lib.checkout("111", alice.member_id, TODAY)
        lib.return_book("111", alice.member_id, TODAY + timedelta(days=2))
        second = lib.checkout("222", alice.member_id, TODAY + timedelta(days=5))
        third = lib.checkout("333", alice.member_id, TODAY + timedelta(days=7))
        assert lib.member_history(alice.member_id) == [third, second, first]

    def test_member_history_only_includes_that_member(self, lib, alice):
        bob = lib.register_member("Bob")
        lib.checkout("111", bob.member_id, TODAY)
        assert lib.member_history(alice.member_id) == []


class TestStorage:
    def test_save_then_load_gives_an_equal_library(self, lib, alice, tmp_path):
        lib.register_member("Bob")
        lib.checkout("222", alice.member_id, TODAY)
        lib.checkout("111", alice.member_id, TODAY)
        lib.return_book("111", alice.member_id, TODAY + timedelta(days=20))
        path = tmp_path / "library.json"
        storage.save_library(lib, path)
        assert storage.load_library(path) == lib

    def test_dates_and_enums_are_stored_as_text(self, lib, alice, tmp_path):
        lib.checkout("222", alice.member_id, TODAY)
        path = tmp_path / "library.json"
        storage.save_library(lib, path)
        text = path.read_text(encoding="utf-8")
        json.loads(text)
        assert "2026-10-01" in text
        assert "SCIENCE" in text


def test_library_methods_have_type_hints():
    missing = []
    for name, func in inspect.getmembers(Library, inspect.isfunction):
        if name.startswith("_"):
            continue
        sig = inspect.signature(func)
        for param in list(sig.parameters.values())[1:]:
            if param.annotation is inspect.Parameter.empty:
                missing.append(f"{name}({param.name})")
        if sig.return_annotation is inspect.Signature.empty:
            missing.append(f"{name} -> ?")
    assert not missing, f"Add type hints: {', '.join(missing)}"


def test_library_does_not_call_date_today():
    assert "date.today" not in inspect.getsource(library_module), (
        "Pass `today` in as a parameter instead of calling date.today()"
    )
