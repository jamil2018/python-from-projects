# 01 · Tip Calculator

Split a restaurant bill between friends, including tip.

## Concepts
- `print()` and `input()`
- Variables and the basic types: `str`, `int`, `float`, `bool`
- Converting between types: `int()`, `float()`, `str()`
- Arithmetic: `+ - * / // % **`
- f-strings and number formatting (`f"{x:.2f}"`)
- `if` / `elif` / `else`, comparison operators

## Core requirements
1. Ask for the total bill amount (e.g. `84.50`).
2. Ask for the tip percentage (e.g. `15`).
3. Ask how many people are splitting the bill.
4. Print the tip amount, the total including tip, and what each person pays, all rounded to 2 decimal places.
5. If the number of people is less than 1, print an error message instead of dividing.

## Example session
```
Welcome to the tip calculator!
Total bill: 84.50
Tip percentage (e.g. 10, 15, 20): 20
How many people? 3

Tip:          16.90
Total:       101.40
Each person:  33.80
```

## Done when
- [ ] All three inputs are converted to the right numeric type
- [ ] Output is formatted to exactly 2 decimal places
- [ ] Entering `0` people prints a friendly error and doesn't crash

## Stretch goals
- Print a rating based on the tip: under 10% "stingy", 10–20% "standard", over 20% "generous".
- Let the user enter the tip as either `15` or `15%`. Hint: `str.rstrip`.
- Round each person's share *up* to the nearest cent so the group never underpays. Hint: `math.ceil`.

## Automated checks
The checks run `main.py` as a separate program and type answers into it, just like a person would:
- Write your program in `main.py`.
- Ask exactly three questions, in this order: bill, tip percentage, number of people.
- Print the tip, the total, and the per-person amount with exactly 2 decimals (`16.90`, not `16.9`).
- With 0 or a negative number of people, print a message and finish normally (no traceback).

```powershell
python -m pytest spec_tests -v
```

## Reflect
What happens if you type `abc` for the bill? Write down the error name you get. You'll learn to handle it in project 02.
