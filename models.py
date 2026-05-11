"""
models.py
---------
Defines the core data models for TaskFlow: Task and Project classes.

This module implements the object-oriented design of the application,
encapsulating task and project attributes along with their behaviors.
"""

from datetime import datetime, date
from enum import Enum


class Priority(Enum):
    """Enumeration of task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def label(self) -> str:
        """Return a display-friendly label for the priority.

        Returns:
            str: Capitalized priority name.
        """
        return self.name.capitalize()


class Status(Enum):
    """Enumeration of task status values."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"

    def label(self) -> str:
        """Return a display-friendly label for the status.

        Returns:
            str: Human-readable status string.
        """
        labels = {
            "todo": "To Do",
            "in_progress": "In Progress",
            "done": "Done",
            "archived": "Archived",
        }
        return labels[self.value]


class Task:
    """Represents a single actionable task within a project.

    Attributes:
        task_id (int): Unique identifier for the task.
        title (str): Short descriptive title.
        description (str): Detailed description of the task.
        priority (Priority): Priority level (LOW, MEDIUM, HIGH, CRITICAL).
        status (Status): Current status of the task.
        due_date (date | None): Optional deadline for the task.
        created_at (datetime): Timestamp when the task was created.
        tags (list[str]): List of keyword tags for filtering.
    """

    def __init__(
        self,
        task_id: int,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        due_date: date | None = None,
        tags: list | None = None,
    ):
        """Initialize a Task instance.

        Args:
            task_id (int): Unique ID assigned by the project.
            title (str): Short title of the task.
            description (str, optional): Longer description. Defaults to "".
            priority (Priority, optional): Task priority. Defaults to MEDIUM.
            due_date (date | None, optional): Deadline. Defaults to None.
            tags (list | None, optional): Keyword tags. Defaults to None.
        """
        self.task_id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.status = Status.TODO
        self.due_date = due_date
        self.created_at = datetime.now()
        self.tags = tags if tags is not None else []

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def is_overdue(self) -> bool:
        """Check whether the task is past its due date and not done.

        Returns:
            bool: True if overdue, False otherwise.
        """
        if self.due_date and self.status not in (Status.DONE, Status.ARCHIVED):
            return date.today() > self.due_date
        return False

    @property
    def days_until_due(self) -> int | None:
        """Calculate the number of days remaining until the due date.

        Returns:
            int | None: Days remaining, or None if no due date is set.
        """
        if self.due_date:
            return (self.due_date - date.today()).days
        return None

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def complete(self) -> None:
        """Mark the task as done."""
        self.status = Status.DONE

    def start(self) -> None:
        """Mark the task as in progress."""
        self.status = Status.IN_PROGRESS

    def archive(self) -> None:
        """Archive the task."""
        self.status = Status.ARCHIVED

    def add_tag(self, tag: str) -> None:
        """Add a tag to the task if it does not already exist.

        Args:
            tag (str): Tag string to add.
        """
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the task to a JSON-compatible dictionary.

        Returns:
            dict: All task fields in serializable form.
        """
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Deserialize a task from a dictionary (e.g., loaded from JSON).

        Args:
            data (dict): Dictionary with task fields.

        Returns:
            Task: Reconstructed Task instance.
        """
        due = date.fromisoformat(data["due_date"]) if data.get("due_date") else None
        task = cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data.get("description", ""),
            priority=Priority[data["priority"]],
            due_date=due,
            tags=data.get("tags", []),
        )
        task.status = Status(data["status"])
        task.created_at = datetime.fromisoformat(data["created_at"])
        return task

    def __repr__(self) -> str:
        return (
            f"Task(id={self.task_id}, title='{self.title}', "
            f"priority={self.priority.label()}, status={self.status.label()})"
        )


class Project:
    """Represents a project containing a collection of tasks.

    Attributes:
        project_id (int): Unique identifier for the project.
        name (str): Project name.
        description (str): Short description of the project.
        created_at (datetime): When the project was created.
        tasks (list[Task]): All tasks belonging to this project.
        _next_task_id (int): Internal counter for task ID generation.
    """

    def __init__(self, project_id: int, name: str, description: str = ""):
        """Initialize a Project instance.

        Args:
            project_id (int): Unique project ID.
            name (str): Project name.
            description (str, optional): Project description. Defaults to "".
        """
        self.project_id = project_id
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.tasks: list[Task] = []
        self._next_task_id: int = 1

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, title: str, description: str = "",
                 priority: Priority = Priority.MEDIUM,
                 due_date: date | None = None,
                 tags: list | None = None) -> Task:
        """Create and add a new task to this project.

        Args:
            title (str): Task title.
            description (str, optional): Task description. Defaults to "".
            priority (Priority, optional): Priority level. Defaults to MEDIUM.
            due_date (date | None, optional): Deadline. Defaults to None.
            tags (list | None, optional): Tags. Defaults to None.

        Returns:
            Task: The newly created Task.
        """
        task = Task(
            task_id=self._next_task_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags,
        )
        self.tasks.append(task)
        self._next_task_id += 1
        return task

    def get_task(self, task_id: int) -> Task | None:
        """Retrieve a task by its ID.

        Args:
            task_id (int): The task's unique ID.

        Returns:
            Task | None: The matching task, or None if not found.
        """
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def remove_task(self, task_id: int) -> bool:
        """Remove a task from the project by ID.

        Args:
            task_id (int): ID of the task to remove.

        Returns:
            bool: True if removed successfully, False if not found.
        """
        original_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < original_len

    # ------------------------------------------------------------------
    # Filtering & statistics (uses list comprehensions)
    # ------------------------------------------------------------------

    def get_tasks_by_status(self, status: Status) -> list[Task]:
        """Return all tasks matching a given status.

        Args:
            status (Status): The status to filter by.

        Returns:
            list[Task]: Filtered list of tasks.
        """
        return [t for t in self.tasks if t.status == status]

    def get_tasks_by_priority(self, priority: Priority) -> list[Task]:
        """Return all tasks matching a given priority.

        Args:
            priority (Priority): The priority to filter by.

        Returns:
            list[Task]: Filtered list of tasks.
        """
        return [t for t in self.tasks if t.priority == priority]

    def get_overdue_tasks(self) -> list[Task]:
        """Return all tasks that are currently overdue.

        Returns:
            list[Task]: List of overdue tasks.
        """
        return [t for t in self.tasks if t.is_overdue]

    def get_tasks_by_tag(self, tag: str) -> list[Task]:
        """Return all tasks that contain a given tag.

        Args:
            tag (str): Tag string to search.

        Returns:
            list[Task]: Matching tasks.
        """
        tag = tag.strip().lower()
        return [t for t in self.tasks if tag in t.tags]

    def sorted_tasks(self, key: str = "priority", reverse: bool = True) -> list[Task]:
        """Return tasks sorted by a given attribute.

        Supports sorting by 'priority', 'due_date', and 'created_at'.

        Args:
            key (str): Sort key. Defaults to 'priority'.
            reverse (bool): Descending order if True. Defaults to True.

        Returns:
            list[Task]: Sorted task list.
        """
        sort_map = {
            "priority": lambda t: t.priority.value,
            "due_date": lambda t: (t.due_date is None, t.due_date or date.max),
            "created_at": lambda t: t.created_at,
        }
        sorter = sort_map.get(key, sort_map["priority"])
        return sorted(self.tasks, key=sorter, reverse=reverse)

    @property
    def completion_rate(self) -> float:
        """Calculate the percentage of tasks that are completed.

        Returns:
            float: Completion rate between 0.0 and 100.0.
        """
        if not self.tasks:
            return 0.0
        done = sum(1 for t in self.tasks if t.status == Status.DONE)
        return (done / len(self.tasks)) * 100

    @property
    def summary(self) -> dict:
        """Generate a summary dictionary of project statistics.

        Returns:
            dict: Counts per status, overdue count, and completion rate.
        """
        return {
            "total": len(self.tasks),
            "todo": len(self.get_tasks_by_status(Status.TODO)),
            "in_progress": len(self.get_tasks_by_status(Status.IN_PROGRESS)),
            "done": len(self.get_tasks_by_status(Status.DONE)),
            "overdue": len(self.get_overdue_tasks()),
            "completion_rate": round(self.completion_rate, 1),
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the project and all its tasks to a dictionary.

        Returns:
            dict: Project fields and serialized tasks list.
        """
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "_next_task_id": self._next_task_id,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Deserialize a project from a dictionary.

        Args:
            data (dict): Dictionary with project fields and tasks.

        Returns:
            Project: Reconstructed Project instance.
        """
        project = cls(
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
        )
        project.created_at = datetime.fromisoformat(data["created_at"])
        project._next_task_id = data.get("_next_task_id", 1)
        project.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return project

    def __repr__(self) -> str:
        return f"Project(id={self.project_id}, name='{self.name}', tasks={len(self.tasks)})"