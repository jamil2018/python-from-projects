import json
from pathlib import Path
from turtle import update

DB_FILE_PATH = Path(__file__).parent / "tasks.json"


def load_file(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def save_file(path: Path, data: list) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def list_tasks(data: list[dict]) -> None:
    if not data:
        print("No tasks yet.")
        return
    for task in data:
        checkbox = ""
        if task.get("done") == False:
            checkbox = "[ ]"
        else:
            checkbox = "[x]"

        priority = task.get("priority", "low")
        print(f'#{task["id"]} {checkbox} ({priority}) {task["title"]}')


def add_task(data: dict) -> None:
    tasks = load_file(DB_FILE_PATH)
    tasks.append(data)
    save_file(DB_FILE_PATH, tasks)
    print(f"added task: {data}")


def complete_task(id: int) -> None:
    tasks = load_file(DB_FILE_PATH)
    found = False
    for task in tasks:
        if task["id"] == id:
            task["done"] = True
            found = True
            break

    if found == False:
        print(f"Requested task with id: {id} not found")
        return

    save_file(DB_FILE_PATH, tasks)
    print(f"Updated task status with id: {id}")


def delete_task(id: int) -> None:
    tasks = load_file(DB_FILE_PATH)
    found = False

    updated_tasks = [task for task in tasks if task["id"] != id]

    if len(tasks) - 1 == len(updated_tasks):
        found = True

    if found == False:
        print(f"Requested task with id: {id} not found")
        return

    save_file(DB_FILE_PATH, updated_tasks)
    print(f"Deleted task with id: {id}")


def edit_task_title(id: int, updated_title: str) -> None:
    tasks = load_file(DB_FILE_PATH)
    found = False
    for task in tasks:
        if task["id"] == id:
            task["title"] = updated_title
            found = True
            break

    if found == False:
        print(f"Requested task with id: {id} not found")
        return

    save_file(DB_FILE_PATH, tasks)
    print(f"Updated task title with id: {id}")


data = load_file(DB_FILE_PATH)
list_tasks(data)
add_task({"id": 1, "title": "Buy cheese", "done": False, "priority": "medium"})
complete_task(1)
delete_task(1)
edit_task_title(2, "This is a test")
