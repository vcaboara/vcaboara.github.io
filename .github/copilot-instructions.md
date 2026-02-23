# Repository Working Context (Updated 2026-02-22)

## Branching and Release Rules

- Do not commit directly to `main`.
- Use a branch workflow and PRs for all changes.
- `main` is protected and should remain production-safe.
- A `stable` tag exists for release anchoring.

## Local Guardrails

- Install hooks with:
  - `powershell -ExecutionPolicy Bypass -File .\utils\install_git_hooks.ps1`
- Hooks enforce:
  - no commits on `main`/`master`
  - no direct pushes to `main`/`master`
  - sensitive-data checks and structural sanity checks

## Test Requirements

- For content/layout changes, run:
  - `python validate_ledger.py`
  - `python validate_compliance_tracker.py`
  - `python validate_mandates.py`
  - `python validate_anchors.py`
- When changing anchor IDs, update `validate_anchors.py` requirements.
- New work should include new tests; updates should include updated tests.

## PR UI Change Policy

- PRs that modify UI-facing files (`.html`, `.css`, `.scss`, `.sass`, `.jsx`, `.tsx`) must include:
  - BEFORE screenshot(s)
  - AFTER screenshot(s)
- Enforced by:
  - `.github/workflows/pr-checks.yml`
  - `utils/check_pr_ui_screenshots.py`

## Shell Preference on Windows

- Prefer Git Bash (`bash.exe`) for shell-compatible hook checks and *nix parity.
- Use PowerShell for Windows-native setup/automation scripts.
