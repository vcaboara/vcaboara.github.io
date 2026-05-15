#!/usr/bin/env python3
"""
Generic pull request creator using GitHub CLI.

This helper intentionally stays lightweight:
- no hardcoded branch names
- no page-specific assumptions
- relies on CI for validators and screenshot-diff checks
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=capture,
    )


def get_current_branch() -> str:
    result = run_command(["git", "branch", "--show-current"], capture=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def has_uncommitted_changes() -> bool:
    result = run_command(["git", "status", "--porcelain"], capture=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def gh_available() -> bool:
    result = run_command(["gh", "--version"], capture=True)
    return result.returncode == 0


def create_pr(base: str, head: str, title: str, body_file: str | None, draft: bool, push: bool) -> int:
    if not gh_available():
        logger.error("GitHub CLI (gh) not found. Install from https://cli.github.com")
        return 1

    if not head:
        logger.error("Could not detect current branch.")
        return 1

    if head in {"main", "master"}:
        logger.error("Refusing to create PR from protected branch.")
        return 1

    if has_uncommitted_changes():
        logger.warning("Working tree has uncommitted changes. Commit or stash first for predictable PR content.")

    if push:
        logger.info(f"Pushing branch '{head}'...")
        push_result = run_command(
            ["git", "push", "-u", "origin", head], capture=True)
        if push_result.returncode != 0:
            logger.error("Failed to push branch.")
            if push_result.stderr:
                logger.error(push_result.stderr.strip())
            elif push_result.stdout:
                logger.error(push_result.stdout.strip())
            return 1

    cmd = [
        "gh",
        "pr",
        "create",
        "--base",
        base,
        "--head",
        head,
        "--title",
        title,
    ]

    if body_file:
        cmd.extend(["--body-file", body_file])
    if draft:
        cmd.append("--draft")

    logger.info(f"Creating PR from '{head}' to '{base}'...")
    result = run_command(cmd, capture=True)

    if result.returncode != 0:
        logger.error("PR creation failed.")
        if result.stderr:
            logger.error(result.stderr.strip())
        return result.returncode

    logger.info("PR created successfully:")
    logger.info(result.stdout.strip())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a pull request with GitHub CLI")
    parser.add_argument("--base", default="main",
                        help="Target/base branch (default: main)")
    parser.add_argument(
        "--head", help="Source branch (default: current branch)")
    parser.add_argument("--title", required=True, help="PR title")
    parser.add_argument("--body-file", help="Optional PR body markdown file")
    parser.add_argument("--draft", action="store_true",
                        help="Create PR as draft")
    parser.add_argument("--push", action="store_true",
                        help="Push source branch before creating PR")
    args = parser.parse_args()

    head = args.head or get_current_branch()
    return create_pr(
        base=args.base,
        head=head,
        title=args.title,
        body_file=args.body_file,
        draft=args.draft,
        push=args.push,
    )


if __name__ == "__main__":
    sys.exit(main())
