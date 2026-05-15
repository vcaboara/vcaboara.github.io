# Testing & Pre-commit Hooks

## Automated Tests

### Browser-based Tests

#### Compliance Tracker Tests
Open `test/test_compliance_tracker.html` in a browser to run:
- Master ticker real-time updates (100ms intervals)
- Toggle switch functionality
- Card rendering (5 corporate cards)
- Color transitions (loss/savings)
- Calculation accuracy (15% license fees, burn per second)
- Data integrity (companies array)
- Glassmorphism styling verification
- Responsive grid layout

### Python Validation

#### Compliance Tracker Validation
```bash
python test/validate_compliance_tracker.py
```

Checks for:
- **Companies data integrity** (5 companies with required fields)
- **Required HTML elements** (master ticker, toggle, cards grid)
- **Calculation accuracy** (15% fees, burn per second formula)
- **Glassmorphism styling** (backdrop-filter applied)
- **Color transition classes** (.loss/.savings)
- **Update intervals** (100ms for ticker)
- **Footer references** (ACS 12/17/2025, AIF 85%)

#### Mandates Validation
```bash
python test/validate_mandates.py
```

Checks for:
- **HTML structure** (pillar cards, logic boxes, footer)
- **All 5 pillars present** with correct titles
- **Key technical content** (12/17 Patent, 15/15 model, 85% funding, staff benefits)
- **Proper mission statement** with social shield terminology
- **Date and footer references** (12/17/2025, tagline)

#### Anchor ID Validation
```bash
python test/validate_anchors.py
```

Checks for:
- **Stable deep-link IDs** on all core pages
- **Missing expected anchors** (fails validation)
- **Duplicate IDs** (warns for cleanup)

## Pre-commit Hook

A versioned pre-commit hook is stored at `.githooks/pre-commit` and can be enabled locally with:

```bash
powershell -ExecutionPolicy Bypass -File .\utils\install_git_hooks.ps1
```

The hook automatically:

1. **Blocks commits on `main`/`master`** (requires branch + PR workflow)
2. **Validates** HTML structure
3. **Validates** compliance tracker data integrity (companies array structure)

### Testing the Hook

Stage a change and try to commit:
```bash
git add compliance-tracker.html
git commit -m "test"
```

If issues are found, the commit will be blocked with details.

### Pre-push Protection

A pre-push hook at `.githooks/pre-push` blocks direct pushes to `main`/`master`.

To test locally:

```bash
echo "refs/heads/dev abc refs/heads/main def" | sh .githooks/pre-push
```

Expected: push is blocked with an error.

### Windows Shell Note

On Windows, prefer Git Bash (`bash.exe`) for direct hook script execution examples.

```powershell
& "C:\Program Files\Git\bin\bash.exe" -lc "cd '$PWD'; ./.githooks/pre-commit"
& "C:\Program Files\Git\bin\bash.exe" -lc "cd '$PWD'; echo 'refs/heads/dev abc refs/heads/main def' | ./.githooks/pre-push"
```

Alternatively, hooks run automatically through `git commit` / `git push` once installed with `core.hooksPath`.

### Bypass (Emergency Only)

To skip pre-commit checks:
```bash
git commit --no-verify -m "message"
```

**⚠️ Use sparingly - bypasses all safety checks!**

## Running Tests Before Push

```bash
# Run Python validations
python test/validate_compliance_tracker.py
python test/validate_mandates.py
python test/validate_anchors.py

# Open browser tests
start test/test_compliance_tracker.html   # Windows
# or
open test/test_compliance_tracker.html    # Mac/Linux
```

## CI/CD Integration

PR checks are now automated via `.github/workflows/pr-checks.yml`:
1. Runs Python validators (`test/validate_compliance_tracker.py`, `test/validate_mandates.py`, `test/validate_anchors.py`)
2. Enforces UI screenshot policy for PRs touching UI-facing files (`.html/.css/.scss/.sass/.jsx/.tsx`)
3. Fails PRs missing BEFORE/AFTER screenshot evidence for UI changes

PR template: `.github/pull_request_template.md`

### UI Screenshot Requirement

If a PR changes UI-facing files, the PR body must include:
- **BEFORE** section
- **AFTER** section
- At least two screenshot images total

Enforcement script: `tools/check_pr_ui_screenshots.py`

### Important: Hooks vs GitHub Required Checks

- Local hooks (`pre-commit`, `pre-push`) run only on developer machines.
- GitHub **required checks** come from CI workflows (for example, GitHub Actions).
- To enforce checks in PRs, create workflow jobs and add those job names to branch protection `required_status_checks`.
