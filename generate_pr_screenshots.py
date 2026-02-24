#!/usr/bin/env python3
"""
Generic screenshot generator for local PR evidence.

Examples:
  python generate_pr_screenshots.py
  python generate_pr_screenshots.py --page index.html=home-after.png --page off-the-shelf.html
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def start_http_server(port: int, cwd: Path) -> subprocess.Popen[bytes]:
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    return process


def parse_page_specs(page_specs: list[str]) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    if not page_specs:
        return [("index.html", "index.png"), ("off-the-shelf.html", "off-the-shelf.png")]

    for spec in page_specs:
        if "=" in spec:
            page, output_name = spec.split("=", 1)
            targets.append((page.strip(), output_name.strip()))
        else:
            page = spec.strip()
            output_name = f"{Path(page).stem}.png"
            targets.append((page, output_name))
    return targets


def capture_screenshot(url: str, output_path: Path, full_page: bool) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright; python -m playwright install chromium")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1800})
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=str(output_path), full_page=full_page)
            browser.close()
        print(f"✅ Saved: {output_path}")
        return True
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"❌ Failed screenshot for {url}: {exc}")
        return False


def generate_screenshots(port: int, output_dir: Path, targets: list[tuple[str, str]], full_page: bool) -> bool:
    repo_root = Path(__file__).parent
    server = start_http_server(port=port, cwd=repo_root)
    try:
        base_url = f"http://127.0.0.1:{port}"
        all_ok = True
        for page, output_name in targets:
            page_path = repo_root / page
            if not page_path.exists():
                print(f"❌ Page not found: {page}")
                all_ok = False
                continue
            target_path = output_dir / output_name
            ok = capture_screenshot(f"{base_url}/{page}", target_path, full_page=full_page)
            all_ok = all_ok and ok

        if all_ok:
            print(f"\n✅ Screenshot generation complete. Output dir: {output_dir}")
        return all_ok
    finally:
        server.terminate()
        server.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local screenshots for PR evidence")
    parser.add_argument("--port", type=int, default=8000, help="Local HTTP server port (default: 8000)")
    parser.add_argument("--output-dir", default="pr-screenshots", help="Output directory (default: pr-screenshots)")
    parser.add_argument(
        "--page",
        action="append",
        default=[],
        help="Page spec: path.html or path.html=filename.png (can repeat)",
    )
    parser.add_argument("--no-full-page", action="store_true", help="Disable full-page screenshots")
    args = parser.parse_args()

    targets = parse_page_specs(args.page)
    output_dir = Path(args.output_dir)
    ok = generate_screenshots(
        port=args.port,
        output_dir=output_dir,
        targets=targets,
        full_page=not args.no_full_page,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
