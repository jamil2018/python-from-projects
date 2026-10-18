# 06 · Bank Accounts

Model a small bank with different account types. This is your introduction to **object-oriented programming**.

**Builds on 05:** modules, data modeling.

## Concepts
- `class`, `__init__`, `self`, instance vs. class attributes
- Methods
- Inheritance, `super()`, and method overriding
- `@property` for read-only or validated attributes
- Dunder methods: `__str__`, `__repr__`, `__eq__`
- Custom exceptions (`class InsufficientFundsError(Exception)`)
- `raise`, plus `try` / `except` / `else` / `finally`
- `decimal.Decimal` for money (and why floats are a bad fit for it)

## Project layout
```
06-bank-accounts/
  accounts.py    # Account classes and exceptions
  bank.py        # Bank class that manages accounts
  main.py        # interactive menu
```

## Core requirements

### `Account` (base class)
- Attributes: `account_number` (auto-generated and unique), `owner`, `balance` (read-only property), `transactions` (a list).
- `deposit(amount)`: the amount must be positive, otherwise raise `ValueError`.
- `withdraw(amount)`: raise `InsufficientFundsError` if the balance is too low.
- Every deposit and withdrawal records a transaction (type, amount, timestamp, resulting balance).
- `__str__` returns something like `Savings #1003 (Alice): $1,250.00`.

### `SavingsAccount(Account)`
- Has an `interest_rate`, the yearly rate as a `Decimal` (for example `Decimal("0.06")` for 6%). `apply_interest()` adds one month of interest (`balance * rate / 12`, rounded to the cent) and marks the end of the month.
- At most 3 withdrawals per month. The 4th raises `WithdrawalLimitError`. The count resets when `apply_interest()` is called. A failed withdrawal doesn't count.

### `CheckingAccount(Account)`
- Has an `overdraft_limit`, so the balance may go down to `-overdraft_limit`.
- Withdrawals that go below zero charge a $25 fee, recorded as its own transaction of type `"fee"`. The withdrawal plus the fee must fit within the overdraft limit. If they don't, raise `InsufficientFundsError` and change nothing.

### `Bank`
- `open_account(kind, owner, initial_deposit)` returns the new account.
- `get(account_number)` raises `AccountNotFoundError` if the number doesn't exist.
- `transfer(from_no, to_no, amount)` must be **all-or-nothing**: if the withdrawal fails, no money moves.
- `total_deposits()` returns the sum of all balances.

### `main.py`
A menu for opening accounts, depositing, withdrawing, transferring, viewing statement history, and applying monthly interest. Every exception is caught and shown as a friendly message.

## Done when
- [ ] Setting `account.balance = 1000000` directly is not possible
- [ ] Both subclasses override `withdraw` and use `super()`
- [ ] All three custom exceptions inherit from one `BankError` base class
- [ ] Money uses `Decimal`, so `0.1 + 0.2` problems can't happen
- [ ] A failed transfer leaves both balances unchanged

## Stretch goals
- Save and load the bank to JSON. You'll need to convert objects to and from dicts (`to_dict` / `from_dict` classmethods).
- Add `__lt__` so accounts can be sorted by balance with `sorted(bank.accounts)`.
- Print a monthly statement with an opening balance, each transaction, and a closing balance.

## Automated checks
The checks import `accounts.py` and `bank.py`. They assume:
- `accounts.py` defines `Account`, `SavingsAccount`, `CheckingAccount`, `BankError`, `InsufficientFundsError`, `WithdrawalLimitError`, and `AccountNotFoundError`.
- Constructors: `Account(owner)`, `SavingsAccount(owner, interest_rate=Decimal("0.02"))`, and `CheckingAccount(owner, overdraft_limit=Decimal("100"))`. New accounts start with a balance of `0`.
- `deposit` and `withdraw` accept a `Decimal`, `int`, `str`, or `float`, converted with `Decimal(str(amount))`. An amount of zero or less raises `ValueError`.
- Each transaction is a dict with the keys `type` (`"deposit"`, `"withdrawal"`, or `"fee"`), `amount`, `timestamp`, and `balance`.
- `__str__` uses the account type's name, for example `Savings #1003 (Alice): $1,250.00` or `Checking #1004 (Bob): $-50.00`.
- Two accounts are `==` when they have the same account number.
- `Bank()` takes no arguments. `open_account(kind, owner, initial_deposit=0)` accepts `"savings"` or `"checking"` in any capitalization and raises `ValueError` for anything else.

```powershell
python -m pytest spec_tests -v
```

## Reflect
Compare this with the dict-based students in project 05. What did classes give you? What felt like extra ceremony? Project 07 introduces `dataclasses`, which remove much of that ceremony.
