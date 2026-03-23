"""SAM session management — stateful CLI session with undo/redo and history."""

import json
import os
from copy import deepcopy
from pathlib import Path


class Session:
    """Stateful session for the SAM REPL.

    Tracks the currently open project, maintains undo/redo history,
    and provides session persistence across REPL commands.
    """

    MAX_HISTORY = 50

    def __init__(self, session_file: str = None):
        """Initialize an empty session.

        Args:
            session_file: Optional path for session persistence (JSON).
        """
        self.project = None
        self.project_path = None
        self.modified = False
        self._history = []       # stack of (project_snapshot, description)
        self._redo_stack = []
        self.last_results = None
        self._session_file = session_file

    # ── Project management ────────────────────────────────────────────

    def open_project(self, project: dict, path: str = None):
        """Set the current project."""
        self.project = project
        self.project_path = path
        self.modified = False
        self._history.clear()
        self._redo_stack.clear()
        self.last_results = project.get("results")

    def close_project(self):
        """Clear the current project."""
        self.project = None
        self.project_path = None
        self.modified = False
        self._history.clear()
        self._redo_stack.clear()
        self.last_results = None

    def update_project(self, new_project: dict, description: str = ""):
        """Update the project, saving current state to undo history."""
        if self.project is not None:
            self._history.append((deepcopy(self.project), description))
            if len(self._history) > self.MAX_HISTORY:
                self._history.pop(0)
        self._redo_stack.clear()
        self.project = new_project
        self.modified = True

    # ── Undo / Redo ───────────────────────────────────────────────────

    def undo(self) -> tuple:
        """Undo the last change.

        Returns:
            (success: bool, description: str)
        """
        if not self._history:
            return False, "Nothing to undo"
        snapshot, description = self._history.pop()
        self._redo_stack.append((deepcopy(self.project), description))
        self.project = snapshot
        self.modified = True
        return True, f"Undid: {description}"

    def redo(self) -> tuple:
        """Redo the last undone change."""
        if not self._redo_stack:
            return False, "Nothing to redo"
        snapshot, description = self._redo_stack.pop()
        self._history.append((deepcopy(self.project), description))
        self.project = snapshot
        self.modified = True
        return True, f"Redid: {description}"

    def can_undo(self) -> bool:
        return len(self._history) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def history(self) -> list:
        """Return list of undo history descriptions (most recent last)."""
        return [desc for _, desc in self._history]

    # ── Status ────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return current session status dict."""
        return {
            "project":      self.project.get("name") if self.project else None,
            "project_path": self.project_path,
            "technology":   self.project.get("technology") if self.project else None,
            "financial":    self.project.get("financial") if self.project else None,
            "modified":     self.modified,
            "has_results":  self.last_results is not None,
            "undo_steps":   len(self._history),
            "redo_steps":   len(self._redo_stack),
        }

    def is_open(self) -> bool:
        return self.project is not None

    def context_name(self) -> str:
        """Return a short context string for the REPL prompt."""
        if not self.project:
            return ""
        name = self.project.get("name", "?")
        tech = self.project.get("technology", "")
        return f"{name} ({tech})"

    # ── Persistence ───────────────────────────────────────────────────

    def save_session(self):
        """Save session state to disk."""
        if not self._session_file:
            return
        state = {
            "project_path": self.project_path,
            "modified":     self.modified,
        }
        path = Path(self._session_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(state, f, indent=2)

    def load_session(self) -> dict:
        """Load session state from disk.

        Returns:
            Session state dict (with "project_path" if available).
        """
        if not self._session_file:
            return {}
        path = Path(self._session_file)
        if not path.exists():
            return {}
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {}

    def default_session_file() -> str:
        """Return the default session file path."""
        return str(Path.home() / ".cli-anything-sam" / "session.json")
