"""
Automated test runner for ledger.html
Validates HTML structure and sensitive data patterns
"""
import re
import sys
from pathlib import Path


def check_sensitive_data(file_path):
    """Check for sensitive data patterns that should be redacted"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # Check for individual names in email addresses
    names = ['DGause', 'rmoran', 'jlilley', 'Mark Hagler', 'Ryan Elliott']
    for name in names:
        if name in content and 'stacy' not in name.lower():
            # Allow 'stacy' only if it's redacted
            if f'{name}@' in content or f'{name.lower()}@' in content:
                issues.append(
                    f"⚠️  WARNING: Individual name '{name}' exposed in email address")

    # Check for LLC in company name
    if 'Arboreum Commercial Solutions' in content:
        if not re.search(r'Arboreum Commercial Solutions, LLC', content):
            matches = re.findall(
                r'Arboreum Commercial Solutions(?!, LLC)', content)
            if matches:
                issues.append(
                    f"⚠️  WARNING: 'Arboreum Commercial Solutions' missing ', LLC' in {len(matches)} place(s)")

    return issues


def check_html_structure(file_path):
    """Basic HTML structure validation"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # Check for required elements
    required = [
        (r'<html[^>]*>', '</html>', 'HTML tags'),
        (r'<head>', '</head>', 'HEAD tags'),
        (r'<body>', '</body>', 'BODY tags'),
        (r'id=["\']main-counter["\']', None, 'main-counter element'),
        (r'id=["\']notice-log["\']', None, 'notice-log table'),
    ]

    for pattern, closing, name in required:
        if not re.search(pattern, content):
            issues.append(f"❌ MISSING: {name}")
        elif closing and not re.search(closing, content):
            issues.append(f"❌ UNCLOSED: {name}")

    # Check for balanced details tags
    details_open = len(re.findall(r'<details', content))
    details_close = len(re.findall(r'</details>', content))
    if details_open != details_close:
        issues.append(
            f"❌ UNBALANCED: {details_open} <details> tags but {details_close} </details> tags")

    return issues


def main():
    print("🧪 Running Ledger Validation Tests\n")

    ledger_path = Path(__file__).parent / 'ledger.html'

    if not ledger_path.exists():
        print(f"❌ ERROR: {ledger_path} not found")
        return 1

    all_issues = []

    print("📋 Checking for sensitive data patterns...")
    sensitive_issues = check_sensitive_data(ledger_path)
    all_issues.extend(sensitive_issues)

    print("🔍 Validating HTML structure...")
    structure_issues = check_html_structure(ledger_path)
    all_issues.extend(structure_issues)

    print()

    if not all_issues:
        print("✅ All checks passed!")
        return 0
    else:
        print("Issues found:\n")
        for issue in all_issues:
            print(f"  {issue}")
        print()

        # Critical issues fail the test
        critical = [
            i for i in all_issues if 'CRITICAL' in i or 'MISSING' in i or 'UNBALANCED' in i]
        if critical:
            print(f"❌ {len(critical)} critical issue(s) - FAILED")
            return 1
        else:
            print(f"⚠️  {len(all_issues)} warning(s) - PASSED with warnings")
            return 0


if __name__ == '__main__':
    sys.exit(main())
