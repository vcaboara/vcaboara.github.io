"""
Validation script for mandates.html
Checks for required pillar content, HTML structure, and sensitive data
"""
import re
import sys
from pathlib import Path


def validate_mandates(file_path):
    """Validate the mandates.html file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # Check for sensitive data patterns
    patent_pattern = r'19/' + r'424,' + r'?106'
    if re.search(patent_pattern, content):
        issues.append(
            f"❌ CRITICAL: Patent number [REDACTED] found (should be [REDACTED])")

    # Check for required structural elements
    required_elements = [
        (r'class=["\']pillar-grid', 'Pillar grid container'),
        (r'class=["\']pillar-card', 'Pillar cards'),
        (r'class=["\']logic-box', 'Logic box for mission statement'),
        (r'class=["\']funding-notice', 'Funding notice section'),
        (r'<footer>', 'Footer element'),
    ]

    for pattern, description in required_elements:
        if not re.search(pattern, content):
            issues.append(f"❌ CRITICAL: Missing {description}")

    # Check for all 5 pillars
    pillar_titles = [
        'Environmental Healing & Resource Sovereignty',
        'Universal Sanctuary & Intergenerational Care',
        'The Sovereign Trust & Universal Access',
        'Systemic Reform & Land Back Reparations',
        'The Staff Flywheel & Veteran Support'
    ]

    pillar_count = len(re.findall(r'<section class=["\']pillar-card', content))
    if pillar_count != 5:
        issues.append(
            f"⚠️  WARNING: Expected 5 pillar cards, found {pillar_count}")

    for pillar_title in pillar_titles:
        if pillar_title not in content:
            issues.append(
                f"⚠️  WARNING: Pillar title not found: '{pillar_title}'")

    # Check for key technical content
    required_content = [
        ('12/17 Patent', 'Patent implementation reference'),
        # regex for multi-line content
        (r'15/15\s+ACS.*?Toll', 'Revenue model reference', True),
        ('85% AIF Endowment', 'Funding mechanism reference'),
        ('agricultural waste', 'Environmental pillar content'),
        # regex for potentially multi-line
        (r'debt-free.*?PhD', 'Educational benefits content', True),
        ('6-hour "Peak Performance" shifts', 'Staff flywheel content'),
        ('biochar soil injection', 'Environmental restoration method'),
        ('Land Back', 'Reparations content'),
    ]

    for item in required_content:
        if len(item) == 3:  # regex pattern
            content_pattern, description, is_regex = item
            if not re.search(content_pattern, content, re.DOTALL):
                issues.append(
                    f"⚠️  WARNING: Missing key content - {description}: '{content_pattern}'")
        else:  # simple string
            content_phrase, description = item
            if content_phrase not in content:
                issues.append(
                    f"⚠️  WARNING: Missing key content - {description}: '{content_phrase}'")

    # Check for proper mission statement with key phrases
    mission_phrases = [
        'social shield',
        'Arboreum Commercial Solutions',
        'systemic',
        '85%'
    ]

    mission_found = any(phrase.lower() in content.lower()
                        for phrase in mission_phrases)
    if not mission_found:
        issues.append(
            "⚠️  WARNING: Mission statement may be incomplete or reworded")

    # Check for footer references
    if '12/17/2025' not in content and '12/17' not in content:
        issues.append("⚠️  WARNING: Missing date reference in footer")

    if 'Sovereignty & Stewardship' not in content:
        issues.append("⚠️  WARNING: Missing footer tagline")

    # Check for HTML validity basics
    if content.count('<h3>') != content.count('</h3>'):
        issues.append("❌ CRITICAL: Mismatched h3 tags")

    if content.count('<section') != content.count('</section>'):
        issues.append("❌ CRITICAL: Mismatched section tags")

    # Report results
    critical_count = sum(1 for issue in issues if "❌" in issue)
    warning_count = sum(1 for issue in issues if "⚠️" in issue)

    return issues, critical_count, warning_count


if __name__ == '__main__':
    file_path = Path(__file__).parent / 'mandates.html'

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    print("🧪 Running Mandates Validation Tests\n")
    print("📋 Checking pillar structure, content integrity, and HTML validity...\n")

    issues, critical_count, warning_count = validate_mandates(file_path)

    if issues:
        print("Issues found:\n")
        for issue in issues:
            print(f"  {issue}")
        print()

    if critical_count > 0:
        print(f"❌ {critical_count} critical issue(s)")
        sys.exit(1)
    elif warning_count > 0:
        print(f"⚠️  {warning_count} warning(s) - PASSED with warnings")
        sys.exit(0)
    else:
        print("✅ All checks passed!")
        sys.exit(0)
