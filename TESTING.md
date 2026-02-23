# Testing & Pre-commit Hooks

## Automated Tests

### Browser-based Tests

#### Ledger Tests
Open `test_ledger.html` in a browser to run the full test suite:
- Counter updates
- Table rendering  
- Collapsible sections
- Value updates without DOM rebuild
- Section collapse state tracking

#### Compliance Tracker Tests
Open `test_compliance_tracker.html` in a browser to run:
- Master ticker real-time updates (100ms intervals)
- Toggle switch functionality
- Card rendering (5 corporate cards)
- Color transitions (loss/savings)
- Calculation accuracy (15% license fees, burn per second)
- Data integrity (companies array)
- Glassmorphism styling verification
- Responsive grid layout

### Python Validation

#### Ledger Validation
```bash
python validate_ledger.py
```

Checks for:
- **Sensitive data leaks** (patent numbers, individual names)
- **HTML structure** (required elements, balanced tags)
- **Company name format** (LLC inclusion)

#### Compliance Tracker Validation
```bash
python validate_compliance_tracker.py
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
python validate_mandates.py
```

Checks for:
- **Sensitive data leaks** (patent numbers)
- **HTML structure** (pillar cards, logic boxes, footer)
- **All 5 pillars present** with correct titles
- **Key technical content** (12/17 Patent, 15/15 model, 85% funding, staff benefits)
- **Proper mission statement** with social shield terminology
- **Date and footer references** (12/17/2025, tagline)

## Pre-commit Hook

A versioned pre-commit hook is stored at `.githooks/pre-commit` and can be enabled locally with:

```bash
powershell -ExecutionPolicy Bypass -File .\utils\install_git_hooks.ps1
```

The hook automatically:

1. **Blocks commits on `main`/`master`** (requires branch + PR workflow)
2. **Blocks commits** containing sensitive patent number (format: XX/XXX,XXX)
3. **Warns** about individual names in email addresses
4. **Validates** HTML structure
5. **Checks** for proper LLC designation in company name
6. **Validates** compliance tracker data integrity (companies array structure)

### Testing the Hook

Stage a change and try to commit:
```bash
git add ledger.html
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
python validate_ledger.py
python validate_compliance_tracker.py
python validate_mandates.py

# Open browser tests
start test_ledger.html               # Windows
start test_compliance_tracker.html   # Windows
# or
open test_ledger.html                # Mac/Linux
open test_compliance_tracker.html    # Mac/Linux
```

## CI/CD Integration

To add GitHub Actions or similar CI:
1. Add `validate_ledger.py` to workflow
2. Add headless browser test runner for `test_ledger.html`
3. Block PRs that fail validation

### Important: Hooks vs GitHub Required Checks

- Local hooks (`pre-commit`, `pre-push`) run only on developer machines.
- GitHub **required checks** come from CI workflows (for example, GitHub Actions).
- To enforce checks in PRs, create workflow jobs and add those job names to branch protection `required_status_checks`.
