"""
Compare UI screenshots between PR base and head revisions.

Behavior:
- If no UI-facing files changed: pass with a short summary.
- If UI files changed but no comparable HTML pages changed: pass with a note.
- If comparable HTML pages changed: capture base/head screenshots, compute pixel diffs,
  and produce a markdown report that can be posted as a PR comment.
"""

from __future__ import annotations

import argparse
import functools
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageChops


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


@dataclass
class PageDiffResult:
    page: str
    status: str
    diff_percent: float
    notes: str


def run_git_diff(base_sha: str, head_sha: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_ui_file(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith(UI_FILE_PATTERNS):
        return False
    return not any(excluded.lower() in lower for excluded in UI_EXCLUDE_PATTERNS)


def is_comparable_html(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".html") and not any(excluded.lower() in lower for excluded in UI_EXCLUDE_PATTERNS)


def export_revision(revision: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_cmd = ["git", "archive", revision]
    tar_cmd = ["tar", "-x", "-C", str(out_dir)]

    archive_proc = subprocess.Popen(archive_cmd, stdout=subprocess.PIPE)
    try:
        subprocess.run(tar_cmd, stdin=archive_proc.stdout, check=True)
    finally:
        if archive_proc.stdout:
            archive_proc.stdout.close()
        archive_proc.wait()


class LocalServer:
    def __init__(self, directory: Path, port: int):
        self.directory = directory
        self.port = port
        self.httpd: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def __enter__(self) -> "LocalServer":
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(self.directory))
        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.6)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.thread:
            self.thread.join(timeout=2)


def capture_screenshot(url: str, output_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1800})
        page.goto(url, wait_until="networkidle")
        page.screenshot(path=str(output_path), full_page=True)
        browser.close()


def compute_diff(base_img_path: Path, head_img_path: Path, diff_img_path: Path) -> tuple[float, str]:
    with Image.open(base_img_path).convert("RGB") as base_img, Image.open(head_img_path).convert("RGB") as head_img:
        if base_img.size != head_img.size:
            target_size = (max(base_img.width, head_img.width), max(base_img.height, head_img.height))
            base_canvas = Image.new("RGB", target_size, (255, 255, 255))
            head_canvas = Image.new("RGB", target_size, (255, 255, 255))
            base_canvas.paste(base_img, (0, 0))
            head_canvas.paste(head_img, (0, 0))
            base_img = base_canvas
            head_img = head_canvas
            size_note = f"resized for compare ({target_size[0]}x{target_size[1]})"
        else:
            size_note = "same dimensions"

        diff_img = ImageChops.difference(base_img, head_img)
        diff_gray = diff_img.convert("L")
        histogram = diff_gray.histogram()
        total_pixels = base_img.width * base_img.height
        changed_pixels = total_pixels - histogram[0]
        diff_percent = (changed_pixels / total_pixels) * 100 if total_pixels else 0.0

        if changed_pixels > 0:
            diff_img_path.parent.mkdir(parents=True, exist_ok=True)
            diff_img.save(diff_img_path)

    return diff_percent, size_note


def write_summary(
    output_markdown: Path,
    ui_changed_files: list[str],
    comparable_pages: list[str],
    results: list[PageDiffResult],
) -> None:
    lines: list[str] = []
    lines.append("## UI Screenshot Diff Report")
    lines.append("")

    if not ui_changed_files:
        lines.append("No UI-facing files changed in this PR.")
        output_markdown.write_text("\n".join(lines), encoding="utf-8")
        return

    lines.append("### UI Files Changed")
    for changed_file in ui_changed_files:
        lines.append(f"- {changed_file}")
    lines.append("")

    if not comparable_pages:
        lines.append("No comparable HTML page changes detected for screenshot diff.")
        output_markdown.write_text("\n".join(lines), encoding="utf-8")
        return

    lines.append("### Visual Comparison")
    lines.append("| Page | Result | Diff % | Notes |")
    lines.append("|---|---:|---:|---|")
    for result in results:
        icon = "✅" if result.status == "no-visible-change" else "🟡" if result.status == "changed" else "❌"
        lines.append(f"| {result.page} | {icon} {result.status} | {result.diff_percent:.3f}% | {result.notes} |")

    changed_pages = [r.page for r in results if r.status == "changed"]
    lines.append("")
    if changed_pages:
        lines.append("### Summary")
        lines.append(f"Visual changes detected on {len(changed_pages)} page(s):")
        for page in changed_pages:
            lines.append(f"- {page}")
    else:
        lines.append("### Summary")
        lines.append("No visible pixel differences detected on comparable pages.")

    output_markdown.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output-markdown", default="ui-screenshot-diff-summary.md")
    parser.add_argument("--artifacts-dir", default="pr-screenshots/ci-diff")
    parser.add_argument("--base-port", type=int, default=8765)
    parser.add_argument("--head-port", type=int, default=8766)
    args = parser.parse_args()

    output_markdown = Path(args.output_markdown)
    artifacts_dir = Path(args.artifacts_dir)

    try:
        changed_files = run_git_diff(args.base_sha, args.head_sha)
    except subprocess.CalledProcessError as exc:
        print("❌ Failed to list changed files")
        print(exc.stderr)
        return 1

    ui_changed_files = [f for f in changed_files if is_ui_file(f)]
    comparable_pages = [f for f in changed_files if is_comparable_html(f)]

    if not ui_changed_files or not comparable_pages:
        write_summary(output_markdown, ui_changed_files, comparable_pages, [])
        print(output_markdown.read_text(encoding="utf-8"))
        return 0

    work_dir = Path(tempfile.mkdtemp(prefix="ui-diff-"))
    base_dir = work_dir / "base"
    head_dir = work_dir / "head"

    results: list[PageDiffResult] = []

    try:
        export_revision(args.base_sha, base_dir)
        export_revision(args.head_sha, head_dir)

        from playwright.sync_api import Error as PlaywrightError  # type: ignore

        with LocalServer(base_dir, args.base_port), LocalServer(head_dir, args.head_port):
            for page in comparable_pages:
                base_page = base_dir / page
                head_page = head_dir / page
                if not base_page.exists() or not head_page.exists():
                    results.append(PageDiffResult(page=page, status="skipped", diff_percent=0.0, notes="page missing in one revision"))
                    continue

                base_img = artifacts_dir / "base" / f"{Path(page).stem}.png"
                head_img = artifacts_dir / "head" / f"{Path(page).stem}.png"
                diff_img = artifacts_dir / "diff" / f"{Path(page).stem}.png"

                try:
                    capture_screenshot(f"http://127.0.0.1:{args.base_port}/{page}", base_img)
                    capture_screenshot(f"http://127.0.0.1:{args.head_port}/{page}", head_img)
                    diff_percent, size_note = compute_diff(base_img, head_img, diff_img)
                    status = "changed" if diff_percent > 0 else "no-visible-change"
                    notes = size_note + ("; diff image saved" if diff_percent > 0 else "")
                    results.append(PageDiffResult(page=page, status=status, diff_percent=diff_percent, notes=notes))
                except (PlaywrightError, OSError, RuntimeError) as exc:
                    results.append(PageDiffResult(page=page, status="error", diff_percent=0.0, notes=str(exc)))

    except subprocess.CalledProcessError as exc:
        print("❌ Failed to export git revisions")
        print(exc.stderr)
        return 1
    finally:
        write_summary(output_markdown, ui_changed_files, comparable_pages, results)
        shutil.rmtree(work_dir, ignore_errors=True)

    print(output_markdown.read_text(encoding="utf-8"))

    if any(result.status == "error" for result in results):
        print("❌ One or more pages failed screenshot comparison")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
