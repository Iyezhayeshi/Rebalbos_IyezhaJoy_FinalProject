"""
main.py
-------
Entry point for TaskFlow — a Command Line Interface Task & Project Manager.

Run with:
    python src/main.py

TaskFlow lets you organise work into projects, add and manage tasks,
track progress, sort and search tasks, and export project data to CSV.

Concepts demonstrated:
- Classes & OOP       : Task, Project, StorageManager
- File Handling       : JSON persistence, CSV export (context managers)
- Data Structures     : list, dict, enum
- Algorithms          : Merge sort (see utils.merge_sort_tasks)
- List Comprehensions : Filtering tasks by status, priority, tag, etc.
"""

import os
import sys

# Allow `python src/main.py` to find sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from models import Project, Priority, Status # pyright: ignore[reportMissingImports]
from storage import StorageManager, StorageError # pyright: ignore[reportMissingImports]
from utils import ( # pyright: ignore[reportMissingImports]
    BOLD, CYAN, BLUE, GREEN, YELLOW, RED, GREY, RESET,
    colorize, print_header, print_task_row, print_task_detail,
    print_project_summary, merge_sort_tasks, search_tasks,
    prompt, prompt_int, prompt_date, prompt_priority,
    prompt_status, confirm, print_error, print_success,
)


# ======================================================================
# Application state
# ======================================================================

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "taskflow_data.json")

storage         = StorageManager(DATA_FILE)
projects: list[Project] = []
next_project_id: int     = 1
active_project: Project | None = None


# ======================================================================
# Persistence helpers
# ======================================================================

def load_data() -> None:
    """Load all projects from the JSON data file into memory."""
    global projects, next_project_id
    try:
        projects, next_project_id = storage.load_projects()
    except StorageError as exc:
        print_error(f"Could not load data: {exc}")
        projects, next_project_id = [], 1


def save_data() -> None:
    """Persist all in-memory projects back to the JSON data file."""
    try:
        storage.save_projects(projects, next_project_id)
    except StorageError as exc:
        print_error(f"Auto-save failed: {exc}")


# ======================================================================
# Project management screens
# ======================================================================

def list_projects() -> None:
    """Display all projects with their summary statistics."""
    print_header("All Projects")
    if not projects:
        print(colorize("  No projects yet. Create one with 'New Project'.\n", GREY))
        return
    for project in projects:
        print_project_summary(project)


def create_project() -> None:
    """Interactively create a new project."""
    global next_project_id
    print_header("Create New Project")

    name = prompt("Project name")
    if not name:
        print_error("Project name cannot be empty.")
        return

    desc = prompt("Description (optional)")

    project = Project(
        project_id=next_project_id,
        name=name,
        description=desc,
    )
    projects.append(project)
    next_project_id += 1
    save_data()
    print_success(f"Project '{name}' created! (ID: {project.project_id})")


def select_project() -> Project | None:
    """Prompt the user to pick a project from the list.

    Returns:
        Project | None: The selected project, or None if cancelled.
    """
    if not projects:
        print_error("No projects available. Create one first.")
        return None

    print_header("Select a Project")
    for p in projects:
        s = p.summary
        print(f"  {colorize(str(p.project_id), CYAN)}.  {colorize(p.name, BOLD)}  "
              f"{GREY}({s['total']} tasks, {s['completion_rate']}% done){RESET}")

    pid = prompt_int("Enter project ID", 1, max(p.project_id for p in projects))
    if pid is None:
        return None
    result = next((p for p in projects if p.project_id == pid), None)
    if result is None:
        print_error(f"No project with ID {pid}.")
    return result


def delete_project() -> None:
    """Delete a project after user confirmation."""
    project = select_project()
    if project is None:
        return
    if confirm(f"Delete project '{project.name}' and ALL its tasks? This cannot be undone."):
        projects.remove(project)
        save_data()
        print_success(f"Project '{project.name}' deleted.")
    else:
        print(colorize("  Deletion cancelled.", GREY))


# ======================================================================
# Task management screens
# ======================================================================

def task_menu(project: Project) -> None:
    """Display the task management menu for a given project.

    Args:
        project (Project): The currently active project.
    """
    while True:
        print_header(f"Project: {project.name}")
        print_project_summary(project)

        options = [
            ("1", "List tasks"),
            ("2", "Add task"),
            ("3", "View task detail"),
            ("4", "Update task status"),
            ("5", "Edit task"),
            ("6", "Delete task"),
            ("7", "Search tasks"),
            ("8", "Sort & filter tasks"),
            ("9", "Export to CSV"),
            ("0", "← Back to main menu"),
        ]
        for key, label in options:
            print(f"  {colorize('[' + key + ']', CYAN)} {label}")

        choice = prompt("\nChoice").strip()

        if choice == "1":
            list_tasks(project)
        elif choice == "2":
            add_task(project)
        elif choice == "3":
            view_task_detail(project)
        elif choice == "4":
            update_task_status(project)
        elif choice == "5":
            edit_task(project)
        elif choice == "6":
            delete_task(project)
        elif choice == "7":
            search_tasks_screen(project)
        elif choice == "8":
            sort_filter_tasks(project)
        elif choice == "9":
            export_csv(project)
        elif choice == "0":
            break
        else:
            print_error("Invalid choice.")


def list_tasks(project: Project, tasks: list | None = None) -> None:
    """Display all (or a given subset of) tasks in the project.

    Args:
        project (Project): The active project.
        tasks (list | None): Optional pre-filtered task list. If None,
                             all project tasks are displayed.
    """
    print_header(f"Tasks — {project.name}")
    task_list = tasks if tasks is not None else project.tasks

    if not task_list:
        print(colorize("  No tasks to display.\n", GREY))
        return

    for i, task in enumerate(task_list, 1):
        print_task_row(task, index=i)
    print()


def add_task(project: Project) -> None:
    """Interactively add a new task to the project."""
    print_header("Add New Task")

    title = prompt("Task title")
    if not title:
        print_error("Task title cannot be empty.")
        return

    description = prompt("Description (optional)")
    priority    = prompt_priority()
    due_date    = prompt_date("Due date")

    tags_raw = prompt("Tags (comma-separated, optional)")
    tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    task = project.add_task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        tags=tags,
    )
    save_data()
    print_success(f"Task '{title}' added! (ID: {task.task_id})")


def _pick_task(project: Project) -> object | None:
    """Helper: Prompt user to enter a task ID within this project.

    Args:
        project (Project): The project to pick a task from.

    Returns:
        Task | None: Found task, or None.
    """
    if not project.tasks:
        print_error("This project has no tasks yet.")
        return None

    task_id = prompt_int("Enter task ID", 1, max(t.task_id for t in project.tasks))
    if task_id is None:
        return None
    task = project.get_task(task_id)
    if task is None:
        print_error(f"No task with ID {task_id}.")
    return task


def view_task_detail(project: Project) -> None:
    """Display the full detail view for a chosen task."""
    task = _pick_task(project)
    if task:
        print_task_detail(task)


def update_task_status(project: Project) -> None:
    """Interactively change the status of an existing task."""
    task = _pick_task(project)
    if not task:
        return

    print_header(f"Update Status — {task.title}")
    print(f"  Current status: {colorize(task.status.label(), YELLOW)}\n")
    print("  New status:")

    new_status = prompt_status()
    if new_status is None:
        return

    task.status = new_status
    save_data()
    print_success(f"Task #{task.task_id} status updated to '{new_status.label()}'.")


def edit_task(project: Project) -> None:
    """Interactively edit the fields of an existing task."""
    task = _pick_task(project)
    if not task:
        return

    print_header(f"Edit Task #{task.task_id}")
    print(f"  Leave any field blank to keep the current value.\n")

    new_title = prompt(f"Title", task.title)
    if new_title:
        task.title = new_title

    new_desc = prompt(f"Description", task.description or "")
    task.description = new_desc

    print(f"  Current priority: {colorize(task.priority.label(), CYAN)}")
    if confirm("Change priority?"):
        task.priority = prompt_priority()

    print(f"  Current due date: {task.due_date or 'None'}")
    if confirm("Change due date?"):
        task.due_date = prompt_date("New due date")

    print(f"  Current tags: {', '.join('#' + t for t in task.tags) if task.tags else 'None'}")
    if confirm("Replace tags?"):
        tags_raw   = prompt("New tags (comma-separated)")
        task.tags  = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]

    save_data()
    print_success(f"Task #{task.task_id} updated.")


def delete_task(project: Project) -> None:
    """Delete a task from the project after confirmation."""
    task = _pick_task(project)
    if not task:
        return

    if confirm(f"Delete task '{task.title}'?"):
        project.remove_task(task.task_id)
        save_data()
        print_success(f"Task '{task.title}' deleted.")
    else:
        print(colorize("  Deletion cancelled.", GREY))


def search_tasks_screen(project: Project) -> None:
    """Full-text search over all tasks in the project."""
    print_header(f"Search Tasks — {project.name}")
    query = prompt("Search query")
    if not query:
        return

    results = search_tasks(project.tasks, query)
    print(colorize(f"\n  Found {len(results)} result(s) for '{query}':\n", CYAN))
    list_tasks(project, tasks=results)


def sort_filter_tasks(project: Project) -> None:
    """Display tasks sorted or filtered by user-selected criteria."""
    print_header(f"Sort & Filter — {project.name}")

    print(f"  {colorize('Sort by:', BOLD)}")
    sort_options = ["priority", "due_date", "created_at", "title"]
    for i, opt in enumerate(sort_options, 1):
        print(f"    {colorize(str(i), CYAN)}. {opt}")

    sort_choice = prompt("Sort key", "1")
    try:
        sort_key = sort_options[int(sort_choice) - 1]
    except (ValueError, IndexError):
        sort_key = "priority"

    print(f"\n  {colorize('Filter by status:', BOLD)}")
    print(f"    {colorize('0', CYAN)}. All statuses")
    for i, s in enumerate(Status, 1):
        print(f"    {colorize(str(i), CYAN)}. {s.label()}")

    filter_choice = prompt("Status filter", "0")
    filter_status = None
    try:
        idx = int(filter_choice)
        if idx > 0:
            filter_status = list(Status)[idx - 1]
    except (ValueError, IndexError):
        pass

    # Apply filter (list comprehension) then sort (merge sort algorithm)
    filtered = [t for t in project.tasks if filter_status is None or t.status == filter_status]
    sorted_tasks = merge_sort_tasks(filtered, key=sort_key)

    label = f"sorted by {sort_key}" + (f", filtered: {filter_status.label()}" if filter_status else "")
    print(colorize(f"\n  Showing {len(sorted_tasks)} task(s) — {label}:\n", CYAN))
    list_tasks(project, tasks=sorted_tasks)


def export_csv(project: Project) -> None:
    """Export all tasks of the active project to a CSV file."""
    print_header(f"Export CSV — {project.name}")

    default_path = os.path.join(
        os.path.dirname(__file__), "..", "data",
        f"{project.name.replace(' ', '_')}_tasks.csv"
    )
    path = prompt("Export file path", default_path)

    try:
        out = storage.export_project_csv(project, path)
        print_success(f"Exported {len(project.tasks)} tasks to:\n    {out}")
    except Exception as exc:
        print_error(f"Export failed: {exc}")


# ======================================================================
# Main menu
# ======================================================================

BANNER = f"""
{colorize('╔══════════════════════════════════════════╗', BLUE)}
{colorize('║', BLUE)}  {colorize('TaskFlow — CLI Task & Project Manager', BOLD + CYAN)}  {colorize('║', BLUE)}
{colorize('╚══════════════════════════════════════════╝', BLUE)}
"""


def main_menu() -> None:
    """Display and handle the top-level application menu."""
    print(BANNER)

    main_options = [
        ("1", "List all projects"),
        ("2", "Open / manage a project"),
        ("3", "Create new project"),
        ("4", "Delete a project"),
        ("0", "Exit"),
    ]

    while True:
        print(colorize("\n  ── Main Menu ──", BOLD))
        for key, label in main_options:
            print(f"  {colorize('[' + key + ']', CYAN)} {label}")

        choice = prompt("\nChoice").strip()

        if choice == "1":
            list_projects()
        elif choice == "2":
            project = select_project()
            if project:
                task_menu(project)
        elif choice == "3":
            create_project()
        elif choice == "4":
            delete_project()
        elif choice == "0":
            print(colorize("\n  Goodbye! 👋\n", GREEN))
            sys.exit(0)
        else:
            print_error("Invalid choice. Please enter a number from the menu.")


# ======================================================================
# Entry point
# ======================================================================

if __name__ == "__main__":
    load_data()
    try:
        main_menu()
    except KeyboardInterrupt:
        print(colorize("\n\n  Interrupted. Saving data...", YELLOW))
        save_data()
        print(colorize("  Data saved. Goodbye!\n", GREEN))
        sys.exit(0)