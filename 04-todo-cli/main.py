import json
from pathlib import Path

DB_FILE_PATH = Path(__file__).parent / "tasks.json"


def load_tasks(path: Path) -> list:
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Warning: the tasks file is corrupted. Starting with an empty list.")
        return []


def save_tasks(path: Path, tasks: list) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=2)


def print_tasks(tasks: list) -> None:
    if not tasks:
        print("No tasks yet.")
        return
    for task in tasks:
        checkbox = ""
        if task.get("done") == False:
            checkbox = "[ ]"
        else:
            checkbox = "[x]"

        priority = task.get("priority", "low")
        print(f'#{task["id"]} {checkbox} ({priority}) {task["title"]}')


def add_task(tasks: list, title: str, priority: str = "medium") -> dict:
    title = title.strip()
    priority = priority.lower()

    if title == "":
        raise ValueError("Title cannot be empty")

    if priority not in ["low", "medium", "high"]:
        raise ValueError("Unknown priority")

    highest_id = 0
    for task in tasks:
        if task["id"] > highest_id:
            highest_id = task["id"]

    data = {
        "id": highest_id + 1,
        "title": title,
        "done": False,
        "priority": priority,
    }

    tasks.append(data)
    return data


def find_task(tasks: list, task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def complete_task(tasks: list, task_id: int):
    task = find_task(tasks, task_id)
    if task is None:
        return None
    task["done"] = True
    return task


def delete_task(tasks: list, task_id: int):
    task = find_task(tasks, task_id)
    if task is None:
        return None
    tasks.remove(task)
    return task


def edit_task(tasks: list, task_id: int, new_title: str):
    new_title = new_title.strip()
    if new_title == "":
        raise ValueError("Title cannot be empty")

    task = find_task(tasks, task_id)
    if task is None:
        return None
    task["title"] = new_title
    return task


def print_menu() -> None:
    print(
        """
        1. List Tasks
        2. Add Task
        3. Complete Task
        4. Delete a Task
        5. Edit Task Title
        6. Quit
    """
    )


def get_user_menu_selection() -> str:
    while True:
        user_selection = input("Your choice: ")

        if user_selection not in ["1", "2", "3", "4", "5", "6"]:
            print("Invalid Input!!!")
        else:
            return user_selection


def invoke_action(choice: str, tasks: list, path: Path) -> None:
    match choice:
        case "1":
            print_tasks(tasks)
        case "2":
            task_title = input("Enter the title of the task: ")
            priority = input("Set the task priority(low, medium, high): ")

            if priority.strip() == "":
                priority = "medium"

            try:
                task = add_task(tasks, task_title, priority)
                save_tasks(path, tasks)
                print(f'Added task #{task["id"]}.')
            except ValueError:
                print("Invalid title or priority.")

        case "3":
            try:
                task_id = int(input("Enter the id of the task you want to complete: "))
            except ValueError:
                print("Id must be a number!")
                return

            task = complete_task(tasks, task_id)
            if task is None:
                print(f"Requested task with id: {task_id} not found")
                return

            save_tasks(path, tasks)
            print(f'Completed "{task["title"]}".')

        case "4":
            try:
                task_id = int(input("Enter the id of the task you want to remove: "))
            except ValueError:
                print("Id must be a number!")
                return

            task = delete_task(tasks, task_id)
            if task is None:
                print(f"Requested task with id: {task_id} not found")
                return

            save_tasks(path, tasks)
            print(f"Deleted task with id: {task_id}")

        case "5":
            try:
                task_id = int(
                    input("Enter the id of the task you want to update title for: ")
                )
            except ValueError:
                print("Id must be a number!")
                return

            task_title = input("Enter the title of the task: ")
            try:
                task = edit_task(tasks, task_id, task_title)
            except ValueError:
                print("Task title cannot be empty!")
                return

            if task is None:
                print(f"Requested task with id: {task_id} not found")
                return

            save_tasks(path, tasks)
            print(f"Updated task title with id: {task_id}")


def main(path=None):
    if path is None:
        path = DB_FILE_PATH

    tasks = load_tasks(path)

    while True:
        print_menu()
        user_selection = get_user_menu_selection()
        if user_selection == "6":
            print("Bye!")
            break
        invoke_action(user_selection, tasks, path)


if __name__ == "__main__":
    main()
