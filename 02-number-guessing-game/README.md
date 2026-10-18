# 02 · Number Guessing Game

The computer picks a secret number and the player guesses it, getting "higher" or "lower" hints after each guess.

**Builds on 01:** input, conversion, conditionals.

## Concepts
- `while` loops, `for` loops, `range()`
- `break` and `continue`
- The `random` module (`random.randint`)
- `import` statements
- `try` / `except ValueError` for handling invalid input
- Counters and accumulator variables

## Core requirements
1. Pick a random integer between 1 and 100.
2. Repeatedly ask for a guess, replying `Too low`, `Too high`, or `Correct!`.
3. Count the attempts and print the count when the player wins.
4. If the player types something that isn't a number, say so and ask again. Invalid input shouldn't count as an attempt and shouldn't crash the program.
5. After a game, ask `Play again? (y/n)` and start a new game on `y`.

## Example session
```
I'm thinking of a number between 1 and 100.
Your guess: 50
Too high.
Your guess: banana
That's not a number. Try again.
Your guess: 25
Too low.
Your guess: 37
Correct! You got it in 3 attempts.
Play again? (y/n): n
Thanks for playing!
```

## Done when
- [ ] Non-numeric input is handled with `try`/`except`
- [ ] Guesses outside 1–100 get a warning and don't count
- [ ] Replay works, with a fresh secret number each time

## Stretch goals
- Difficulty levels: easy (1–50, unlimited guesses), medium (1–100, 10 guesses), hard (1–500, 8 guesses).
- Track the best score (fewest attempts) across games in one session.
- **Reverse mode:** *you* pick the number and the computer guesses it using binary search. Can it always win in 7 guesses or fewer for 1–100? Why?

## Automated checks
The checks run your `main.py`, type guesses into it, and replace `random.randint` with a fake so they know the secret number:
- Write your program in `main.py`.
- Pick the secret with `random.randint(1, 100)`, called once per game.
- The words `too low`, `too high`, and `correct` must appear in your replies (any capitalization).
- When the player wins, print the attempt count as a number followed by `attempt` or `attempts`, e.g. `3 attempts`.
- Ask `Play again? (y/n)` after each game: `y` starts a new game, `n` ends the program.

```powershell
python -m pytest spec_tests -v
```

## Reflect
Find any code you wrote twice (for example, "ask for a number and validate it"). In the next project you'll learn to turn that into a function.
