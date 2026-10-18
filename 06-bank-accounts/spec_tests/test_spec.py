"""Checks for project 06. Run from the project folder: python -m pytest spec_tests -v"""

import inspect
import re
from decimal import Decimal

import pytest

from accounts import (
    Account,
    AccountNotFoundError,
    BankError,
    CheckingAccount,
    InsufficientFundsError,
    SavingsAccount,
    WithdrawalLimitError,
)
from bank import Bank


@pytest.fixture
def account():
    acc = Account("Alice")
    acc.deposit(Decimal("100"))
    return acc


class TestAccount:
    def test_starts_empty(self):
        acc = Account("Alice")
        assert acc.owner == "Alice"
        assert acc.balance == Decimal("0")
        assert acc.transactions == []

    def test_account_numbers_are_unique(self):
        numbers = {Account("x").account_number for _ in range(5)}
        assert len(numbers) == 5

    def test_deposit_and_withdraw(self, account):
        account.withdraw(Decimal("30"))
        assert account.balance == Decimal("70")

    def test_balance_is_a_decimal(self, account):
        assert isinstance(account.balance, Decimal)

    def test_no_float_rounding_errors(self):
        acc = Account("Alice")
        acc.deposit(0.1)
        acc.deposit(0.2)
        assert acc.balance == Decimal("0.3")

    def test_accepts_strings_and_ints(self):
        acc = Account("Alice")
        acc.deposit("10.50")
        acc.deposit(5)
        assert acc.balance == Decimal("15.50")

    def test_balance_cannot_be_set_directly(self, account):
        with pytest.raises(AttributeError):
            account.balance = Decimal("1000000")

    @pytest.mark.parametrize("amount", [0, -5, "-0.01"])
    def test_amount_must_be_positive(self, account, amount):
        with pytest.raises(ValueError):
            account.deposit(amount)
        with pytest.raises(ValueError):
            account.withdraw(amount)
        assert account.balance == Decimal("100")

    def test_insufficient_funds(self, account):
        with pytest.raises(InsufficientFundsError):
            account.withdraw(Decimal("100.01"))
        assert account.balance == Decimal("100")

    def test_transactions_are_recorded(self, account):
        account.withdraw(Decimal("40"))
        assert len(account.transactions) == 2
        deposit, withdrawal = account.transactions
        assert {"type", "amount", "timestamp", "balance"} <= set(deposit)
        assert deposit["type"] == "deposit" and deposit["amount"] == Decimal("100")
        assert withdrawal["type"] == "withdrawal" and withdrawal["balance"] == Decimal("60")

    def test_failed_withdrawal_is_not_recorded(self, account):
        with pytest.raises(InsufficientFundsError):
            account.withdraw(Decimal("500"))
        assert len(account.transactions) == 1

    def test_equality_is_by_account_number(self, account):
        assert account == account
        assert account != Account("Alice")

    def test_repr_is_not_the_default(self, account):
        assert "object at 0x" not in repr(account)


class TestSavingsAccount:
    def test_str(self):
        acc = SavingsAccount("Alice")
        acc.deposit("1250")
        assert re.fullmatch(rf"Savings #{acc.account_number} \(Alice\): \$1,250\.00", str(acc))

    def test_apply_interest(self):
        acc = SavingsAccount("Alice", interest_rate=Decimal("0.06"))
        acc.deposit("1000")
        acc.apply_interest()
        assert acc.balance == Decimal("1005.00")

    def test_interest_is_rounded_to_the_cent(self):
        acc = SavingsAccount("Alice", interest_rate=Decimal("0.06"))
        acc.deposit("1000.01")
        acc.apply_interest()
        assert acc.balance == Decimal("1005.01")

    def test_fourth_withdrawal_in_a_month_fails(self):
        acc = SavingsAccount("Alice")
        acc.deposit("100")
        for _ in range(3):
            acc.withdraw("10")
        with pytest.raises(WithdrawalLimitError):
            acc.withdraw("10")
        assert acc.balance == Decimal("70")

    def test_limit_resets_after_interest(self):
        acc = SavingsAccount("Alice")
        acc.deposit("100")
        for _ in range(3):
            acc.withdraw("10")
        acc.apply_interest()
        acc.withdraw("10")

    def test_failed_withdrawal_does_not_use_up_the_limit(self):
        acc = SavingsAccount("Alice")
        acc.deposit("100")
        with pytest.raises(InsufficientFundsError):
            acc.withdraw("1000")
        for _ in range(3):
            acc.withdraw("10")

    def test_cannot_overdraw(self):
        acc = SavingsAccount("Alice")
        acc.deposit("50")
        with pytest.raises(InsufficientFundsError):
            acc.withdraw("60")


class TestCheckingAccount:
    def test_str(self):
        acc = CheckingAccount("Bob")
        acc.deposit("20")
        assert re.fullmatch(rf"Checking #{acc.account_number} \(Bob\): \$20\.00", str(acc))

    def test_withdraw_within_balance_has_no_fee(self):
        acc = CheckingAccount("Bob")
        acc.deposit("50")
        acc.withdraw("50")
        assert acc.balance == Decimal("0")

    def test_overdraft_charges_a_fee(self):
        acc = CheckingAccount("Bob", overdraft_limit=Decimal("100"))
        acc.deposit("50")
        acc.withdraw("100")
        assert acc.balance == Decimal("-75")
        assert acc.transactions[-1]["type"] == "fee"
        assert acc.transactions[-1]["amount"] == Decimal("25")

    def test_withdrawal_plus_fee_must_fit_the_limit(self):
        acc = CheckingAccount("Bob", overdraft_limit=Decimal("100"))
        acc.deposit("50")
        with pytest.raises(InsufficientFundsError):
            acc.withdraw("130")
        assert acc.balance == Decimal("50")


class TestDesign:
    def test_exceptions_share_a_base_class(self):
        for exc in (InsufficientFundsError, WithdrawalLimitError, AccountNotFoundError):
            assert issubclass(exc, BankError)
        assert issubclass(BankError, Exception)

    @pytest.mark.parametrize("cls", [SavingsAccount, CheckingAccount])
    def test_subclasses_override_withdraw_using_super(self, cls):
        assert issubclass(cls, Account)
        assert "withdraw" in cls.__dict__, f"{cls.__name__} should override withdraw()"
        assert "super()" in inspect.getsource(cls.withdraw)


class TestBank:
    @pytest.fixture
    def bank(self):
        return Bank()

    def test_open_account(self, bank):
        acc = bank.open_account("Savings", "Alice", Decimal("100"))
        assert isinstance(acc, SavingsAccount)
        assert acc.balance == Decimal("100")
        assert isinstance(bank.open_account("checking", "Bob"), CheckingAccount)

    def test_unknown_kind(self, bank):
        with pytest.raises(ValueError):
            bank.open_account("crypto", "Alice", Decimal("1"))

    def test_get(self, bank):
        acc = bank.open_account("savings", "Alice", Decimal("100"))
        assert bank.get(acc.account_number) is acc

    def test_get_unknown(self, bank):
        with pytest.raises(AccountNotFoundError):
            bank.get(999999)

    def test_transfer(self, bank):
        a = bank.open_account("checking", "Alice", Decimal("100"))
        b = bank.open_account("checking", "Bob", Decimal("10"))
        bank.transfer(a.account_number, b.account_number, Decimal("40"))
        assert a.balance == Decimal("60")
        assert b.balance == Decimal("50")

    def test_failed_transfer_moves_nothing(self, bank):
        a = bank.open_account("savings", "Alice", Decimal("100"))
        b = bank.open_account("savings", "Bob", Decimal("10"))
        with pytest.raises(InsufficientFundsError):
            bank.transfer(a.account_number, b.account_number, Decimal("500"))
        assert a.balance == Decimal("100")
        assert b.balance == Decimal("10")

    def test_transfer_to_unknown_account_moves_nothing(self, bank):
        a = bank.open_account("savings", "Alice", Decimal("100"))
        with pytest.raises(AccountNotFoundError):
            bank.transfer(a.account_number, 999999, Decimal("50"))
        assert a.balance == Decimal("100")

    def test_total_deposits(self, bank):
        bank.open_account("savings", "Alice", Decimal("100.25"))
        bank.open_account("checking", "Bob", Decimal("50"))
        assert bank.total_deposits() == Decimal("150.25")
