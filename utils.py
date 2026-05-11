"""
utils.py
--------
Utility functions for TaskFlow: display formatting, input validation,
search, and a custom sorting algorithm used across the CLI.

This module demonstrates:
- List comprehensions and generator expressions
- A non-trivial algorithm (merge sort on tasks)
- Input validation helpers
"""

from datetime import date, datetime
from typing import Optional

from models import Task, Project, Priority, Status # pyright: ignore[reportMissingImports]


# ======================================================================
# ANSI colour helpers
# ======================================================================

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
GREY   = "\033[90m"
WHITE  = "\033[97m"


def colorize(text: str, color: str) -> str:
    """Wrap text with an ANSI colour code and reset.

    Args:
        text (str): The string to colorize.
        color (str): ANSI escape code string.

    Returns:
        str: Colorized string.
    """
    return f"{color}{text}{RESET}"


def priority_color(priority: Priority) -> str:
    """Return the ANSI colour associated with a priority level.

    Args:
        priority (Priority): Priority enum value.

    Returns:
        str: ANSI color code.
    """
    mapping = {
        Priority.LOW: GREY,
        Priority.MEDIUM: CYAN,
        Priority.HIGH: YELLOW,
        Priority.CRITICAL: RED,
    }
    return mapping.get(priority, WHITE)


def status_color(status: Status) -> str:
    """Return the ANSI colour associated with a task status.

    Args:
        status (Status): Status enum value.

    Returns:
        str: ANSI color code.
    """
    mapping = {
        Status.TODO: WHITE,
        Status.IN_PROGRESS: YELLOW,
        Status.DONE: GREEN,
        Status.ARCHIVED: GREY,
    }
    return mapping.get(status, WHITE)


# ======================================================================
# Table display
# ======================================================================

def print_header(title: str) -> None:
    """Print a styled section header.

    Args:
        title (str): Header title text.
    """
    width = 60
    print()
    print(colorize("=" * width, BLUE))
    print(colorize(f"  {title}", BOLD + CYAN))
    print(colorize("=" * width, BLUE))


def print_task_row(task: Task, index: Optional[int] = None) -> None:
    """Print a single task as a formatted table row.

    Args:
        task (Task): The task to display.
        index (int | None): Optional display index prefix.
    """
    prefix = f"{GREY}[{index}]{RESET} " if index is not None else ""
    p_color = priority_color(task.priority)
    s_color = status_color(task.status)

    priority_str = colorize(f"[{task.priority.label():<8}]", p_color)
    status_str   = colorize(f"{task.status.label():<11}", s_color)
    title_str    = colorize(task.title, BOLD)

    due_str = ""
    if task.due_date:
        days = task.days_until_due
        if task.is_overdue:
            due_str = colorize(f" ⚠ OVERDUE ({abs(days)}d ago)", RED)
        elif days == 0:
            due_str = colorize(" ⚑ Due TODAY", YELLOW)
        elif days <= 3:
            due_str = colorize(f" ⚑ Due in {days}d", YELLOW)
        else:
            due_str = colorize(f" Due: {task.due_date}", GREY)

    tags_str = ""
    if task.tags:
        tags_str = colorize("  #" + " #".join(task.tags), GREY)

    print(f"  {prefix}{priority_str} {status_str} {title_str}{due_str}{tags_str}")


def print_task_detail(task: Task) -> None:
    """Print full detail view of a single task.

    Args:
        task (Task): The task to display in detail.
    """
    print_header(f"Task #{task.task_id} — {task.title}")

    p_color = priority_color(task.priority)
    s_color = status_color(task.status)

    rows = [
        ("Priority",    colorize(task.priority.label(), p_color)),
        ("Status",      colorize(task.status.label(), s_color)),
        ("Created",     task.created_at.strftime("%Y-%m-%d %H:%M")),
        ("Due Date",    str(task.due_date) if task.due_date else "—"),
        ("Tags",        ", ".join(f"#{t}" for t in task.tags) if task.tags else "—"),
        ("Description", task.description or "—"),
    ]

    for label, value in rows:
        print(f"  {colorize(label + ':', BOLD)} {value}")

    if task.is_overdue:
        print(colorize(f"\n  ⚠ This task is OVERDUE by {abs(task.days_until_due)} day(s)!", RED))
    print()


def print_project_summary(project: Project) -> None:
    """Print a summary card for a project.

    Args:
        project (Project): The project to summarise.
    """
    s = project.summary
    bar = _progress_bar(s["completion_rate"])

    print(f"  {colorize(project.name, BOLD + CYAN)}  {GREY}(ID: {project.project_id}){RESET}")
    if project.description:
        print(f"  {GREY}{project.description}{RESET}")

    stats = (
        f"  {colorize(str(s['total']), WHITE)} tasks | "
        f"{colorize(str(s['todo']), WHITE)} todo | "
        f"{colorize(str(s['in_progress']), YELLOW)} in-progress | "
        f"{colorize(str(s['done']), GREEN)} done"
    )
    if s["overdue"] > 0:
        stats += f" | {colorize(str(s['overdue']) + ' overdue', RED)}"

    print(stats)
    print(f"  {bar}  {colorize(str(s['completion_rate']) + '%', GREEN)}")
    print()


def _progress_bar(pct: float, width: int = 20) -> str:
    """Render an ASCII progress bar.

    Args:
        pct (float): Percentage complete (0–100).
        width (int): Character width of the bar. Defaults to 20.

    Returns:
        str: Formatted coloured progress bar string.
    """
    filled = int((pct / 100) * width)
    bar    = "█" * filled + "░" * (width - filled)
    color  = GREEN if pct >= 75 else (YELLOW if pct >= 40 else RED)
    return f"[{colorize(bar, color)}]"


# ======================================================================
# Non-trivial algorithm: Merge Sort on tasks
# ======================================================================

def merge_sort_tasks(tasks: list[Task], key: str = "priority") -> list[Task]:
    """Sort a list of tasks using the merge sort algorithm.

    Merge sort is used here (rather than Python's built-in sort) to
    demonstrate an O(n log n) divide-and-conquer sorting algorithm.

    The base case is a list of length 0 or 1, which is already sorted.
    The recursive case splits the list, sorts each half, and merges.

    Args:
        tasks (list[Task]): The tasks to sort.
        key (str): Attribute to sort by. One of:
            'priority'   — highest priority first
            'due_date'   — earliest due date first (None last)
            'created_at' — newest first
            'title'      — alphabetical

    Returns:
        list[Task]: A new sorted list of tasks.
    """
    # Base case: a list of 0 or 1 element is already sorted
    if len(tasks) <= 1:
        return tasks

    key_funcs = {
        "priority":   lambda t: -t.priority.value,             # descending
        "due_date":   lambda t: (t.due_date is None, t.due_date or date.max),
        "created_at": lambda t: t.created_at,
        "title":      lambda t: t.title.lower(),
    }
    get_key = key_funcs.get(key, key_funcs["priority"])

    # Divide
    mid   = len(tasks) // 2
    left  = merge_sort_tasks(tasks[:mid], key)
    right = merge_sort_tasks(tasks[mid:], key)

    # Conquer (merge)
    return _merge(left, right, get_key)


def _merge(left: list[Task], right: list[Task], get_key) -> list[Task]:
    """Merge two sorted task lists into one sorted list.

    Args:
        left (list[Task]): Left sorted partition.
        right (list[Task]): Right sorted partition.
        get_key (callable): Key function for comparison.

    Returns:
        list[Task]: Merged sorted list.
    """
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if get_key(left[i]) <= get_key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # Append any remaining elements (list comprehension style)
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ======================================================================
# Search
# ======================================================================

def search_tasks(tasks: list[Task], query: str) -> list[Task]:
    """Full-text search over task titles, descriptions, and tags.

    Uses a list comprehension with an inner generator to check each
    searchable field efficiently.

    Args:
        tasks (list[Task]): Pool of tasks to search.
        query (str): Search string (case-insensitive).

    Returns:
        list[Task]: Tasks that contain the query in any searchable field.
    """
    q = query.strip().lower()
    searchable_fields = lambda t: [
        t.title.lower(),
        t.description.lower(),
        *t.tags,
    ]
    return [t for t in tasks if any(q in field for field in searchable_fields(t))]


# ======================================================================
# Input validation helpers
# ======================================================================

def prompt(message: str, default: str = "") -> str:
    """Display a prompt and return stripped user input.

    Args:
        message (str): Prompt message shown to the user.
        default (str): Value to return if the user enters nothing.

    Returns:
        str: User input or default value.
    """
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"  {CYAN}>{RESET} {message}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return value if value else default


def prompt_int(message: str, min_val: int = 1, max_val: int = 9999) -> Optional[int]:
    """Prompt the user for an integer within a given range.

    Args:
        message (str): Prompt text.
        min_val (int): Minimum acceptable value. Defaults to 1.
        max_val (int): Maximum acceptable value. Defaults to 9999.

    Returns:
        int | None: Validated integer, or None on cancellation.
    """
    while True:
        raw = prompt(f"{message} ({min_val}–{max_val}, or 'q' to cancel)")
        if raw.lower() == "q":
            return None
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(colorize(f"  Please enter a number between {min_val} and {max_val}.", RED))
        except ValueError:
            print(colorize("  Invalid input — please enter a whole number.", RED))


def prompt_date(message: str) -> Optional[date]:
    """Prompt the user for a date in YYYY-MM-DD format.

    Args:
        message (str): Prompt text.

    Returns:
        date | None: Parsed date, or None if skipped.
    """
    while True:
        raw = prompt(f"{message} (YYYY-MM-DD, or press Enter to skip)")
        if not raw:
            return None
        try:
            d = date.fromisoformat(raw)
            if d < date.today():
                confirm = prompt("That date is in the past. Use it anyway? (y/n)", "n")
                if confirm.lower() != "y":
                    continue
            return d
        except ValueError:
            print(colorize("  Invalid date format. Use YYYY-MM-DD.", RED))


def prompt_priority() -> Priority:
    """Prompt the user to select a priority level.

    Returns:
        Priority: Selected Priority enum value. Defaults to MEDIUM.
    """
    print(f"  Priority options: "
          f"{GREY}1-Low{RESET}  "
          f"{CYAN}2-Medium{RESET}  "
          f"{YELLOW}3-High{RESET}  "
          f"{RED}4-Critical{RESET}")
    raw = prompt("Select priority", "2")
    try:
        val = int(raw)
        if 1 <= val <= 4:
            return Priority(val)
    except ValueError:
        pass
    return Priority.MEDIUM


def prompt_status() -> Optional[Status]:
    """Prompt the user to select a task status.

    Returns:
        Status | None: Selected Status, or None if cancelled.
    """
    options = list(Status)
    for i, s in enumerate(options, 1):
        color = status_color(s)
        print(f"  {i}. {colorize(s.label(), color)}")
    raw = prompt("Select status (or 'q' to cancel)")
    if raw.lower() == "q":
        return None
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except (ValueError, IndexError):
        pass
    return None


def confirm(message: str) -> bool:
    """Ask the user a yes/no confirmation question.

    Args:
        message (str): Question text.

    Returns:
        bool: True if user confirms with 'y' or 'yes'.
    """
    raw = prompt(f"{message} (y/n)", "n")
    return raw.lower() in ("y", "yes")


def print_error(message: str) -> None:
    """Print an error message in red.

    Args:
        message (str): Error text.
    """
    print(colorize(f"\n  ✗ {message}", RED))


def print_success(message: str) -> None:
    """Print a success message in green.

    Args:
        message (str): Success text.
    """
    print(colorize(f"\n  ✓ {message}", GREEN))