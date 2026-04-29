"""
Validation script for compliance-tracker.html
Checks for data integrity, required elements, and calculation accuracy
"""
import re
import sys
from pathlib import Path


def validate_compliance_tracker(file_path):
    """Validate the compliance tracker HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # Check for required companies data
    if 'companies = [' not in content:
        issues.append("❌ CRITICAL: Companies data array not found")
    else:
        # Validate company data structure
        companies_match = re.search(
            r'companies = (\[.*?\]);', content, re.DOTALL)
        if companies_match:
            companies_str = companies_match.group(1)

            # Check for 5 companies
            ticker_count = len(re.findall(r'"ticker":', companies_str))
            if ticker_count != 5:
                issues.append(
                    f"⚠️  WARNING: Expected 5 companies, found {ticker_count}")

            # Check for required fields
            required_fields = ['name', 'ticker', 'dailyBurn']
            for field in required_fields:
                if f'"{field}":' not in companies_str:
                    issues.append(
                        f"❌ CRITICAL: Missing '{field}' field in companies data")

            # Validate expected tickers
            expected_tickers = ['IP', 'WRK', 'PKG', 'AVY', 'GPK']
            for ticker in expected_tickers:
                if f'"ticker": "{ticker}"' not in companies_str:
                    issues.append(
                        f"⚠️  WARNING: Expected ticker '{ticker}' not found")

    # Check for required HTML elements
    required_elements = [
        (r'id=["\']master-amount["\']', 'Master ticker element'),
        (r'id=["\']toggle-switch["\']', 'Toggle switch element'),
        (r'id=["\']cards-grid["\']', 'Cards grid container'),
        (r'class=["\']footer["\']', 'Footer section'),
    ]

    for pattern, element_name in required_elements:
        if not re.search(pattern, content):
            issues.append(f"❌ CRITICAL: Missing {element_name}")

    # Check for glassmorphism styles
    if 'backdrop-filter: blur' not in content:
        issues.append("⚠️  WARNING: Glassmorphism backdrop-filter not found")

    # Check for required CSS classes
    required_classes = [
        'master-ticker', 'card', 'toggle-switch', 'metric-value',
        'card-ticker', 'card-name', 'fee-value'
    ]
    for class_name in required_classes:
        if f'.{class_name}' not in content:
            issues.append(
                f"⚠️  WARNING: CSS class '.{class_name}' not defined")

    # Check for color transition classes
    if '.loss' not in content or '.savings' not in content:
        issues.append(
            "❌ CRITICAL: Color transition classes (.loss/.savings) missing")

    # Check for update interval
    if 'setInterval' not in content:
        issues.append("❌ CRITICAL: setInterval for ticker updates not found")
    else:
        # Should update every 100ms
        if 'setInterval(updateMasterTicker, 100)' not in content:
            issues.append(
                "⚠️  WARNING: Ticker update interval may not be 100ms")

    # Check for 15% license fee calculation
    if '0.15' not in content:
        issues.append("⚠️  WARNING: 15% license fee calculation not found")

    # Check for ACS reference in footer
    if 'ACS 12/17/2025' not in content:
        issues.append(
            "⚠️  WARNING: 'ACS 12/17/2025' reference missing from footer")

    # Check for AIF 85% profit mandate reference
    if '85%' not in content or 'AIF' not in content:
        issues.append("⚠️  WARNING: AIF 85% profit mandate reference missing")

    # Check font families
    if "'Inter'" not in content and "'Roboto Mono'" not in content:
        issues.append(
            "⚠️  WARNING: Expected font families (Inter/Roboto Mono) not found")

    # Check for responsive design
    if '@media' not in content:
        issues.append("⚠️  WARNING: No responsive @media queries found")

    # Validate burn per second calculation
    burn_calc_pattern = r'burnPerSecond = totalDailyBurn / 86400'
    if not re.search(burn_calc_pattern, content):
        issues.append(
            "⚠️  WARNING: Burn per second calculation may be incorrect (should divide by 86400)")

    return issues


def main():
    print("🧪 Running Compliance Tracker Validation Tests\n")

    tracker_path = Path(__file__).parent.parent / 'compliance-tracker.html'

    if not tracker_path.exists():
        print(f"❌ ERROR: {tracker_path} not found")
        return 1

    print("📋 Validating compliance-tracker.html structure and calculations...")
    issues = validate_compliance_tracker(tracker_path)

    print()

    if not issues:
        print("✅ All validation checks passed!")
        return 0
    else:
        print("Issues found:\n")
        for issue in issues:
            print(f"  {issue}")
        print()

        # Critical issues fail the test
        critical = [i for i in issues if 'CRITICAL' in i]
        if critical:
            print(f"❌ {len(critical)} critical issue(s) - FAILED")
            return 1
        else:
            print(f"⚠️  {len(issues)} warning(s) - PASSED with warnings")
            return 0


if __name__ == '__main__':
    sys.exit(main())
