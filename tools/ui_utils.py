"""Shared utilities for UI file detection and git operations."""

from __future__ import annotations

import subprocess

UI_FILE_PATTERNS = (
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".jsx",
    ".tsx",
)

UI_EXCLUDE_PATTERNS = (
    "test_",
    "TESTING.md",
)


def run_git_diff(base_sha: str, head_sha: str) -> list[str]:
    """Get list of files changed between two git refs."""
    cmd = ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_ui_file(path: str) -> bool:
    """Check if file is a UI-facing file (HTML, CSS, etc.) not excluded."""
    lower = path.lower()
    if not lower.endswith(UI_FILE_PATTERNS):
        return False

    for excluded in UI_EXCLUDE_PATTERNS:
        if excluded.lower() in lower:
            return False

    return True
