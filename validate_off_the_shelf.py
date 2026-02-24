"""
Validation script for off-the-shelf.html
Checks for required elements, manufacturer data integrity, and structural consistency
"""
import re
import sys
from pathlib import Path


def validate_off_the_shelf(file_path):
    """Validate the off-the-shelf.html file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # Check for required container elements
    required_elements = [
        (r'id=["\']ots-content["\']', 'Main content container'),
        (r'id=["\']ots-header["\']', 'Header element'),
        (r'id=["\']status-badge["\']', 'Status badge'),
        (r'id=["\']ots-nav["\']', 'Navigation'),
        (r'id=["\']ots-main["\']', 'Main section'),
        (r'id=["\']ots-footer["\']', 'Footer element'),
        (r'id=["\']ots-intro["\']', 'Introduction paragraph'),
    ]

    for pattern, element_name in required_elements:
        if not re.search(pattern, content):
            issues.append(f"❌ CRITICAL: Missing {element_name}")

    # Check for all 5 required sections
    required_sections = [
        (r'id=["\']section-thermal["\']', 'Thermal Conversion & Energy Systems'),
        (r'id=["\']section-extraction["\']', 'Extraction & Fractionation Systems'),
        (r'id=["\']section-recovery["\']', 'Resource Recovery & Energy Reclamation'),
        (r'id=["\']section-fiber["\']', 'Fiber Processing & Aqueous Systems'),
        (r'id=["\']section-scada["\']', 'Industrial Control & Compliance (SCADA)'),
    ]

    for pattern, section_name in required_sections:
        if not re.search(pattern, content):
            issues.append(
                f"❌ CRITICAL: Missing section ID for '{section_name}'")

    # Check for all 5 required tables with correct IDs
    required_tables = [
        (r'id=["\']table-thermal["\']', 'Thermal table'),
        (r'id=["\']table-extraction["\']', 'Extraction table'),
        (r'id=["\']table-recovery["\']', 'Recovery table'),
        (r'id=["\']table-fiber["\']', 'Fiber table'),
        (r'id=["\']table-scada["\']', 'SCADA table'),
    ]

    for pattern, table_name in required_tables:
        if not re.search(pattern, content):
            issues.append(
                f"❌ CRITICAL: Missing table ID for {table_name}")

    # Verify manufacturer count per section
    manufacturers = {
        'thermal': 2,
        'extraction': 3,
        'recovery': 4,
        'fiber': 2,
        'scada': 1,
    }

    for section_key, expected_count in manufacturers.items():
        # Extract each table and count rows
        table_pattern = rf'id=["\']table-{section_key}["\'].*?</table>'
        table_match = re.search(table_pattern, content, re.DOTALL)
        if table_match:
            table_content = table_match.group(0)
            row_count = len(re.findall(r'<tr>\s*<td>', table_content))
            if row_count != expected_count:
                issues.append(
                    f"⚠️  WARNING: {section_key} section has {row_count} manufacturers, expected {expected_count}")
        else:
            issues.append(
                f"❌ CRITICAL: Could not find table-{section_key} in content")

    # Check for revenue streams section
    if not re.search(r'id=["\']revenue-streams["\']', content):
        issues.append("❌ CRITICAL: Missing revenue-streams section")
    else:
        # Verify all 5 revenue stream items
        revenue_pattern = r'id=["\']revenue-list["\'].*?</ul>'
        revenue_match = re.search(revenue_pattern, content, re.DOTALL)
        if revenue_match:
            revenue_content = revenue_match.group(0)
            revenue_items = len(re.findall(r'<li>', revenue_content))
            if revenue_items != 5:
                issues.append(
                    f"⚠️  WARNING: Revenue list has {revenue_items} items, expected 5")

    # Check for theme CSS variables
    required_vars = ['--bg', '--card', '--border', '--blue', '--red', '--text', '--high-vis', '--slate']
    for var in required_vars:
        if f'{var}:' not in content:
            issues.append(
                f"⚠️  WARNING: CSS variable '{var}' not defined")

    # Check that all links are valid
    invalid_links = []
    link_pattern = r'href=["\']([^"\']+)["\']'
    for link_match in re.finditer(link_pattern, content):
        link = link_match.group(1)
        # Skip external links (those starting with http)
        if not link.startswith('http'):
            # Check local links exist
            if link in ['index.html', 'Manufacturers.md', 'ledger.html', 'compliance-tracker.html']:
                pass  # These are expected
            elif not link.startswith('http'):
                invalid_links.append(link)

    if invalid_links:
        issues.append(
            f"⚠️  WARNING: Potentially invalid internal links: {', '.join(set(invalid_links))}")

    # Check for required manufacturer links (sample check)
    required_manufacturers = [
        'industrialmicrowave.com',
        'biomassenergytechniques.com',
        'sulzer.com',
        'valmet.com',
        'andritz.com',
        'evapcodc.com',
        'ormat.com',
        'electratherm.com',
        'bronswerk.com',
        'bio-process.com',
        'alfalaval.com',
        'embitel.com',
    ]

    for manufacturer in required_manufacturers:
        if manufacturer not in content:
            issues.append(
                f"⚠️  WARNING: Expected manufacturer '{manufacturer}' not found in content")

    # Check that integration architecture is noted as proprietary
    if 'proprietary' not in content.lower() or 'integration architecture' not in content.lower():
        issues.append(
            "⚠️  WARNING: Footer should note that integration architecture is proprietary and for licensees only")

    # Check for proper table structure
    if '<thead>' not in content or '<tbody>' not in content:
        issues.append("❌ CRITICAL: Tables missing proper thead/tbody structure")

    # Check for all section headings (h2 tags in sections)
    section_headings = len(re.findall(r'<section[^>]*>\s*<h2>', content))
    if section_headings < 5:
        issues.append(
            f"⚠️  WARNING: Expected at least 5 section headings, found {section_headings}")

    return issues


def print_report(issues):
    """Print validation report"""
    if not issues:
        print("✅ All validations passed!")
        return True

    print("📋 Validation Report:")
    print("-" * 60)

    critical = [i for i in issues if 'CRITICAL' in i]
    warnings = [i for i in issues if 'WARNING' in i]

    if critical:
        print("\n🔴 CRITICAL ISSUES:")
        for issue in critical:
            print(f"  {issue}")

    if warnings:
        print("\n🟡 WARNINGS:")
        for issue in warnings:
            print(f"  {issue}")

    print("-" * 60)
    print(
        f"Summary: {len(critical)} critical, {len(warnings)} warning(s)\n")

    return len(critical) == 0


def main():
    """Run validation"""
    file_path = Path(__file__).parent / 'off-the-shelf.html'

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    print(f"🔍 Validating: {file_path}\n")

    issues = validate_off_the_shelf(file_path)
    success = print_report(issues)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
