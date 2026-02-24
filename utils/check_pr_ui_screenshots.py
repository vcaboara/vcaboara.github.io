"""
PR policy check for UI changes.

Rules:
- If UI-facing files changed, PR body must include both BEFORE and AFTER labels.
- PR body must include at least two screenshots (Markdown image or HTML <img> tags).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys


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
    cmd = ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    files = [line.strip()
             for line in result.stdout.splitlines() if line.strip()]
    return files


def is_ui_file(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith(UI_FILE_PATTERNS):
        return False

    for excluded in UI_EXCLUDE_PATTERNS:
        if excluded.lower() in lower:
            return False

    return True


def count_images(pr_body: str) -> int:
    markdown_images = re.findall(r"!\[[^\]]*\]\([^)]+\)", pr_body)
    html_images = re.findall(r"<img\b[^>]*>", pr_body, flags=re.IGNORECASE)
    return len(markdown_images) + len(html_images)


def has_before_after_labels(pr_body: str) -> bool:
    has_before = re.search(r"\bbefore\b", pr_body,
                           flags=re.IGNORECASE) is not None
    has_after = re.search(r"\bafter\b", pr_body,
                          flags=re.IGNORECASE) is not None
    return has_before and has_after


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    args = parser.parse_args()

    try:
        changed_files = run_git_diff(args.base_sha, args.head_sha)
    except subprocess.CalledProcessError as exc:
        print("❌ Unable to determine changed files for PR policy check.")
        print(exc.stderr)
        return 1

    ui_changed_files = [f for f in changed_files if is_ui_file(f)]

    if not ui_changed_files:
        print("✅ No UI-facing file changes detected; screenshot policy not required.")
        return 0

    pr_body = os.environ.get("PR_BODY", "")
    if not pr_body.strip():
        print("❌ UI changes detected, but PR body is empty.")
        print("UI-changed files:")
        for file in ui_changed_files:
            print(f"  - {file}")
        print("Add BEFORE/AFTER screenshots in the PR description.")
        return 1

    image_count = count_images(pr_body)
    labeled = has_before_after_labels(pr_body)

    if not labeled or image_count < 2:
        print("❌ UI changes detected, but screenshot evidence is incomplete.")
        print("UI-changed files:")
        for file in ui_changed_files:
            print(f"  - {file}")
        print()
        print("Required in PR body:")
        print("  - BEFORE label")
        print("  - AFTER label")
        print("  - At least two screenshot images")
        print(f"Detected images: {image_count}")
        return 1

    print("✅ UI screenshot policy satisfied.")
    print("UI-changed files:")
    for file in ui_changed_files:
        print(f"  - {file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
