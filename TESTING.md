# Testing & Pre-commit Hooks

## Automated Tests

### Browser-based Tests
Open `test_ledger.html` in a browser to run the full test suite:
- Counter updates
- Table rendering  
- Collapsible sections
- Value updates without DOM rebuild
- Section collapse state tracking

### Python Validation
```bash
python validate_ledger.py
```

Checks for:
- **Sensitive data leaks** (patent numbers, individual names)
- **HTML structure** (required elements, balanced tags)
- **Company name format** (LLC inclusion)

## Pre-commit Hook

A pre-commit hook is installed at `.git/hooks/pre-commit` that automatically:

1. **Blocks commits** containing sensitive patent number (format: XX/XXX,XXX)
2. **Warns** about individual names in email addresses
3. **Validates** HTML structure
4. **Checks** for proper LLC designation in company name

### Testing the Hook

Stage a change and try to commit:
```bash
git add ledger.html
git commit -m "test"
```

If issues are found, the commit will be blocked with details.

### Bypass (Emergency Only)

To skip pre-commit checks:
```bash
git commit --no-verify -m "message"
```

**⚠️ Use sparingly - bypasses all safety checks!**

## Running Tests Before Push

```bash
# Run Python validation
python validate_ledger.py

# Open browser tests
start test_ledger.html  # Windows
# or
open test_ledger.html   # Mac/Linux
```

## CI/CD Integration

To add GitHub Actions or similar CI:
1. Add `validate_ledger.py` to workflow
2. Add headless browser test runner for `test_ledger.html`
3. Block PRs that fail validation
