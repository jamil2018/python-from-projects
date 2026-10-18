# 04 · Todo List CLI

A menu-driven todo app that saves your tasks to disk, so they're still there the next time you run it.

**Builds on 03:** functions, dicts, file reading.

## Concepts
- Lists of dictionaries as a simple data model
- The `json` module (`json.dump`, `json.load`)
- `pathlib.Path` for file paths
- Program state and a main loop
- `enumerate()`
- Separating data logic from user interaction

## Data model
Each task is a dict:
```python
{"id": 1, "title": "Buy milk", "done": False, "priority": "medium"}
```
All tasks are saved in `tasks.json` next to your script.

## Core requirements
Menu:
```
1. List tasks
2. Add task
3. Complete task
4. Delete task
5. Edit task title
6. Quit
```
1. **List** shows tasks as `[x]` or `[ ]` with their id and priority. If there are none, print "No tasks yet."
2. **Add** asks for a title and a priority (`low`/`medium`/`high`, default `medium`). A new task's id is one more than the highest id in the list (or `1` for an empty list).
3. **Complete**, **Delete**, and **Edit** ask for an id. An unknown id gives a clear message.
4. Save to `tasks.json` after every change. Load on startup. If the file doesn't exist, start with an empty list. If it's corrupted (invalid JSON), warn the user and start empty instead of crashing.

Split your code into at least these functions:
`load_tasks(path)`, `save_tasks(path, tasks)`, `add_task(tasks, title, priority)`, `find_task(tasks, task_id)`, `complete_task(tasks, task_id)`, `delete_task(tasks, task_id)`, `edit_task(tasks, task_id, new_title)`, `print_tasks(tasks)`, `main()`.

## Example session
```
1. List  2. Add  3. Complete  4. Delete  5. Edit  6. Quit
> 2
Title: Write project 04
Priority [low/medium/high] (medium): high
Added task #1.
> 1
  #1 [ ] (high)   Write project 04
> 3
Task id: 1
Completed "Write project 04".
> 6
Bye!
```

## Done when
- [ ] Tasks survive restarting the program
- [ ] Deleting task #2 and then adding a new task doesn't produce a duplicate id
- [ ] Invalid menu choices and ids never crash the program
- [ ] The functions that change `tasks` don't call `input()` or `print()`

## Stretch goals
- Never reuse an id, even after deleting the newest task. You'll need to save the next id alongside the tasks.
- Sort the list by priority, then by done status.
- Add an optional due date (`YYYY-MM-DD`) and flag overdue tasks. Hint: `datetime.date.fromisoformat`.
- "Clear completed" removes all done tasks in one go. Try writing it as a list comprehension (preview of project 05).
- Undo the last action.

## Automated checks
The checks import your functions from `main.py`. They assume:
- `add_task(tasks, title, priority="medium")` appends the new task dict to `tasks` and returns it. Surrounding spaces are stripped from the title, and the priority is lowercased. An empty title or an unknown priority raises `ValueError`.
- `find_task`, `complete_task`, `delete_task`, and `edit_task` return the affected task, or `None` if there's no task with that id. `edit_task` raises `ValueError` for an empty title.
- `load_tasks` returns `[]` for a missing or corrupted file instead of raising.
- `print_tasks` prints `No tasks yet.` for an empty list. Otherwise it prints each task with `[x]` or `[ ]`, `#<id>`, its priority, and its title.
- `main(path=None)` uses `path` as the tasks file, falling back to `tasks.json` next to the script. The checks pass a temporary file so your real tasks are never touched.
- The menu numbers and prompt order match the example session. Edit asks for the id, then the new title.

```powershell
python -m pytest spec_tests -v
```

## Reflect
What would happen if two copies of the program ran at once and both saved? You'll meet a better storage option, a database, in project 10.
