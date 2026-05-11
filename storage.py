"""
storage.py
----------
Handles all file I/O operations for TaskFlow using JSON persistence.

This module provides the StorageManager class, which is responsible for
loading and saving the entire application state (projects and tasks) to
a JSON file. It uses Python context managers for safe file access.
"""

import json
import os
from pathlib import Path
from typing import Optional

from models import Project # pyright: ignore[reportMissingImports]


class StorageError(Exception):
    """Custom exception for storage-related errors."""
    pass


class StorageManager:
    """Manages persistence of project data to a JSON file.

    Uses Python's context manager protocol (via ``open``) to ensure
    file handles are always closed properly, even when errors occur.

    Attributes:
        filepath (Path): Absolute path to the JSON data file.
    """

    def __init__(self, filepath: str = "data/taskflow_data.json"):
        """Initialize StorageManager with a target file path.

        Creates any missing parent directories automatically.

        Args:
            filepath (str): Path to the JSON file used for persistence.
                            Defaults to 'data/taskflow_data.json'.
        """
        self.filepath = Path(filepath)
        self._ensure_directory()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_directory(self) -> None:
        """Create parent directories for the data file if they don't exist."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def _default_structure(self) -> dict:
        """Return an empty data structure for a fresh data file.

        Returns:
            dict: Default app data with empty projects list and counter.
        """
        return {"projects": [], "_next_project_id": 1}

    # ------------------------------------------------------------------
    # Core load / save using context managers
    # ------------------------------------------------------------------

    def load(self) -> dict:
        """Load raw data from the JSON file.

        Uses a context manager to safely open and read the file.
        Returns the default empty structure if the file does not yet exist.

        Returns:
            dict: Parsed JSON data dictionary.

        Raises:
            StorageError: If the file exists but cannot be parsed.
        """
        if not self.filepath.exists():
            return self._default_structure()

        try:
            with open(self.filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"Data file '{self.filepath}' is corrupted: {exc}"
            ) from exc

    def save(self, data: dict) -> None:
        """Write the given data dictionary to the JSON file.

        Uses a context manager for safe file writing. The file is
        written with indentation for human readability.

        Args:
            data (dict): Data to serialize and persist.

        Raises:
            StorageError: If the file cannot be written.
        """
        try:
            with open(self.filepath, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise StorageError(
                f"Could not write to '{self.filepath}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # High-level project operations
    # ------------------------------------------------------------------

    def load_projects(self) -> tuple[list[Project], int]:
        """Load and deserialize all projects from disk.

        Returns:
            tuple[list[Project], int]: A list of Project objects and
                                       the next available project ID.

        Raises:
            StorageError: If the data file cannot be read or parsed.
        """
        data = self.load()
        projects = [Project.from_dict(p) for p in data.get("projects", [])]
        next_id = data.get("_next_project_id", 1)
        return projects, next_id

    def save_projects(self, projects: list[Project], next_project_id: int) -> None:
        """Serialize and save all projects to disk.

        Args:
            projects (list[Project]): Projects to persist.
            next_project_id (int): The next available project ID counter.

        Raises:
            StorageError: If the data file cannot be written.
        """
        data = {
            "projects": [p.to_dict() for p in projects],
            "_next_project_id": next_project_id,
        }
        self.save(data)

    def export_project_csv(self, project: Project, export_path: str) -> str:
        """Export all tasks of a project to a CSV file.

        Uses a context manager to safely write the CSV, producing one
        row per task with all relevant fields.

        Args:
            project (Project): The project whose tasks are exported.
            export_path (str): Destination file path for the CSV.

        Returns:
            str: Absolute path of the written CSV file.

        Raises:
            StorageError: If the file cannot be written.
        """
        import csv

        path = Path(export_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fields = [
            "task_id", "title", "description", "priority",
            "status", "due_date", "created_at", "tags",
        ]

        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fields)
                writer.writeheader()
                for task in project.tasks:
                    row = task.to_dict()
                    row["tags"] = ", ".join(row["tags"])
                    writer.writerow({k: row[k] for k in fields})
        except OSError as exc:
            raise StorageError(f"Could not export CSV: {exc}") from exc

        return str(path.resolve())

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def file_exists(self) -> bool:
        """Check whether the data file exists on disk.

        Returns:
            bool: True if the data file exists.
        """
        return self.filepath.exists()

    def get_file_size_kb(self) -> float:
        """Return the size of the data file in kilobytes.

        Returns:
            float: File size in KB, or 0.0 if the file doesn't exist.
        """
        if self.filepath.exists():
            return self.filepath.stat().st_size / 1024
        return 0.0