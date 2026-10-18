# 05 · Gradebook

Load student scores from a CSV file, compute grades and statistics, and export a report. This is your first project split across **multiple files**.

**Builds on 04:** file persistence, separating logic from I/O.

## Concepts
- Modules: splitting code into files and importing between them
- The `csv` module (`csv.DictReader`, `csv.DictWriter`)
- List, dict, and set comprehensions
- `sorted()` / `.sort()` with `key=` and `lambda`
- `min`, `max`, `sum`, `any`, `all`, `zip`
- Tuples and unpacking
- The `statistics` module (`mean`, `median`, `stdev`)

## Project layout
```
05-gradebook/
  main.py        # menu / user interaction only
  gradebook.py   # loading, saving, calculations (no print/input)
  report.py      # turning results into formatted text
  grades.csv     # input data (create it)
```

## Input data
Create `grades.csv` with at least 10 students:
```csv
name,homework,midterm,final
Alice,92,88,95
Bob,75,64,80
Chen,58,71,62
...
```

## Core requirements
1. Final score = homework 30% + midterm 30% + final 40%. Keep the weights in a dict so they're easy to change.
2. Letter grades: A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, otherwise F.
3. In `gradebook.py`, provide:
   - `load_students(path)` returns a tuple `(students, skipped)`. `students` is a list of dicts with the scores converted to numbers. `skipped` is a list of warning messages, one per bad row, each mentioning the row's line number (the header is line 1).
   - `final_score(student, weights)` returns a float
   - `letter_grade(score)` returns a `str`
   - `class_stats(students)` returns a dict with mean, median, min, max, and stdev of the final scores
   - `grade_distribution(students)` returns a dict like `{"A": 3, "B": 4, ...}`
   - `top_students(students, n)` returns a list sorted by final score, highest first
4. `main.py` offers a menu: show all students (sortable by name or score), show statistics, show distribution, look up a student by name (case-insensitive), and export a report.
5. **Export** writes `report.csv` with columns `name,final,letter`. Put this in `gradebook.export_report(students, path)`.
6. Rows with missing or non-numeric scores are skipped. `main.py` prints the warnings that `load_students` returns.

## Done when
- [ ] `gradebook.py` contains no `print` or `input` calls
- [ ] At least three comprehensions are used where they make the code clearer
- [ ] Sorting uses `key=lambda ...` rather than a hand-written sort
- [ ] A broken row in the CSV doesn't stop the rest from loading

## Stretch goals
- Curve the grades so the class mean becomes 80.
- Show a text histogram of the grade distribution.
- Support any number of assignment columns, with the weights read from a separate `weights.json`.

## Automated checks
The checks import `gradebook.py`. They assume:
- A module-level `WEIGHTS = {"homework": 0.3, "midterm": 0.3, "final": 0.4}`.
- Each student dict has the keys `name`, `homework`, `midterm`, and `final`.
- `class_stats`, `grade_distribution`, and `top_students` take an optional `weights` argument that defaults to `WEIGHTS`.
- `class_stats` returns the keys `mean`, `median`, `min`, `max`, and `stdev`.
- `grade_distribution` always includes all five letters, even when a count is `0`.
- `top_students` returns the student dicts themselves, highest final score first.
- `export_report` writes rows highest score first, with `final` shown to 2 decimals.

```powershell
python -m pytest spec_tests -v
```

## Reflect
Students are dicts with string keys. How many times did you type `student["final"]`? A typo there only fails at runtime. In the next project, classes fix that.
