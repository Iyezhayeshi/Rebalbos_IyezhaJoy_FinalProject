# TaskFlow — CLI Task & Project Manager

> A command-line application for organising projects and tasks, built with pure Python.

**YouTube Demo:** https://youtu.be/oN5yaiD_y_s

---

## Table of Contents

- [Project Description](#project-description)
- [Features](#features)
- [Python Concepts Demonstrated](#python-concepts-demonstrated)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [How to Run](#how-to-run)
- [CLI Usage Guide](#cli-usage-guide)
- [Sample Data](#sample-data)

---

## Project Description

TaskFlow is a fully interactive CLI application that lets you manage real-world
work by organising tasks into projects. Every task carries a priority level,
status, optional deadline, and searchable tags. All data is automatically
saved to a local JSON file so your work persists between sessions.

---

## Features

| Feature | Description |
|---|---|
| **Project Management** | Create, list, and delete projects |
| **Task CRUD** | Add, view, edit, and delete tasks |
| **Priority Levels** | LOW / MEDIUM / HIGH / CRITICAL with colour coding |
| **Status Tracking** | To Do → In Progress → Done → Archived |
| **Due Dates & Overdue Alerts** | Visual warnings for overdue and soon-due tasks |
| **Tags** | Keyword tagging for flexible organisation |
| **Full-Text Search** | Search tasks by title, description, or tag |
| **Sort & Filter** | Sort by priority / due date / created date / title; filter by status |
| **Progress Bar** | Per-project completion percentage and ASCII bar |
| **CSV Export** | Export any project's tasks to a `.csv` file |
| **JSON Persistence** | All data auto-saved; survives application restarts |
| **Error Handling** | Graceful handling of invalid input, missing files, corrupt data |

---

## Python Concepts Demonstrated

### 1. Classes & OOP (`models.py`)
- **`Task`** class — encapsulates task data (id, title, priority, status, due date, tags) and behaviour (`.complete()`, `.start()`, `.is_overdue` property, `.to_dict()` / `.from_dict()`)
- **`Project`** class — owns a list of tasks; exposes filtering, statistics, and serialisation
- **`Priority`** and **`Status`** enumerations using Python's `enum.Enum`
- `@property` decorators for computed attributes (`is_overdue`, `days_until_due`, `completion_rate`, `summary`)
- `@classmethod` for deserialization (`from_dict`)

### 2. File Handling (`storage.py`)
- **Context managers** (`with open(...) as fh`) for safe JSON read/write
- **JSON persistence** — full app state serialized/deserialized on every load/save
- **CSV export** using `csv.DictWriter` inside a context manager
- Custom `StorageError` exception class for meaningful error messages
- `pathlib.Path` for cross-platform directory and file management

### 3. Data Structures & Algorithms (`utils.py`)
- **Merge Sort** — custom recursive implementation to sort task lists
  - Base case: list of 0 or 1 element (already sorted)
  - Recursive case: divide → sort halves → merge
  - Time complexity: **O(n log n)**
- Supports sorting by priority, due date, created date, or title

### 4. List Comprehensions & Generator Expressions (`models.py`, `utils.py`)
```python
# Filtering tasks by status
[t for t in self.tasks if t.status == status]

# Overdue check across all tasks
[t for t in self.tasks if t.is_overdue]

# Full-text search with inner generator
[t for t in tasks if any(q in field for field in searchable_fields(t))]

# Completion rate
sum(1 for t in self.tasks if t.status == Status.DONE) / len(self.tasks) * 100
```

---

## Project Structure

```
Rebalbos_IyezhaJoy_FinalProject/
│
├── README.md                  # This file
├── requirements.txt           # No external dependencies
├── .gitignore
│
├── src/
│   ├── main.py                # Entry point — CLI menus and navigation
│   ├── models.py              # Task, Project, Priority, Status classes
│   ├── storage.py             # JSON & CSV file handling (StorageManager)
│   └── utils.py               # Display, merge sort, search, input prompts
│
└── data/
    └── taskflow_data.json     # Auto-generated persistent data file
```

---

## Installation & Setup

### Requirements
- Python **3.10+** (uses `X | Y` union type hints)
- No external packages required — only the Python standard library

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/TaskFlow_FinalProject.git
cd TaskFlow_FinalProject

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Verify Python version
python --version                # Should be 3.10 or higher
```

No `pip install` step is needed — TaskFlow has zero external dependencies.

---

## How to Run

```bash
python src/main.py
```

> **Note:** Always run from the project root directory so the `data/` folder
> is found correctly.

---

## CLI Usage Guide

### Main Menu

```
╔══════════════════════════════════════════╗
║  TaskFlow — CLI Task & Project Manager  ║
╚══════════════════════════════════════════╝

  ── Main Menu ──
  [1] List all projects
  [2] Open / manage a project
  [3] Create new project
  [4] Delete a project
  [0] Exit
```

### Creating a Project

```
  > Project name: Website Redesign
  > Description (optional): Full redesign for Q3 launch

  ✓ Project 'Website Redesign' created! (ID: 1)
```

### Adding a Task

```
  > Task title: Implement responsive layout
  > Description (optional): Mobile-first CSS grid layout
  Priority options: 1-Low  2-Medium  3-High  4-Critical
  > Select priority [2]: 3
  > Due date (YYYY-MM-DD, or press Enter to skip): 2026-05-10
  > Tags (comma-separated, optional): frontend, css

  ✓ Task 'Implement responsive layout' added! (ID: 3)
```

### Task List View

```
  [1] [High    ] To Do       Implement responsive layout  Due: 2026-05-10  #frontend #css
  [2] [Critical] To Do       Accessibility audit  ⚠ OVERDUE (2d ago)  #a11y #qa
  [3] [Medium  ] In Progress Write homepage copy  #content
```

### Sort & Filter

```
  Sort by:
    1. priority
    2. due_date
    3. created_at
    4. title
  > Sort key [1]: 2

  Filter by status:
    0. All statuses
    1. To Do
    2. In Progress
    3. Done
    4. Archived
  > Status filter [0]: 1
```

### CSV Export

```
  > Export file path [data/Website_Redesign_tasks.csv]:

  ✓ Exported 5 tasks to:
      /home/user/TaskFlow_FinalProject/data/Website_Redesign_tasks.csv
```

### Error Handling Examples

```
  # Invalid menu choice
  ✗ Invalid choice. Please enter a number from the menu.

  # Out-of-range task ID
  ✗ No task with ID 99.

  # Bad date format
  ✗ Invalid date format. Use YYYY-MM-DD.

  # Empty required field
  ✗ Task title cannot be empty.
```

---

## Sample Data

The repository includes pre-loaded sample data in `data/taskflow_data.json`
with two demo projects:

- **Website Redesign** — 5 tasks across all statuses, including one overdue task
- **CS Final Exam Prep** — 4 study tasks with upcoming deadlines

Run the app immediately to explore these projects without entering data manually.

---

_TaskFlow — Individual Machine Project | Python Programming Course_

