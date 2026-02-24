"""
Validation script for stable deep-link anchor IDs across site pages.
Ensures required section/heading IDs exist and warns on duplicate IDs.
"""
import re
import sys
from pathlib import Path


ANCHOR_REQUIREMENTS = {
    "index.html": [
        "home",
        "site-title",
        "primary-links",
        "site-footer",
    ],
    "arboreum.html": [
        "company-header",
        "company-title",
        "partnership-brief",
        "standard-overview",
        "operations-leadership",
        "federal-global-interoperability",
        "patent-status",
        "company-footer",
    ],
    "standard.html": [
        "standard-title",
        "executive-summary",
        "critical-window",
        "regulatory-resolution-matrix",
        "licensing-model",
        "industrial-synergy",
        "patent-authority",
    ],
    "raw_standard.html": [
        "standard-title",
        "executive-summary",
        "regulatory-interoperability",
        "licensing-model",
        "system-status",
        "raw-standard-footer",
    ],
    "legal.html": [
        "virtual-patent-marking",
        "statutory-notice",
        "patent-status",
        "patent-status-heading",
        "legal-footer",
    ],
    "mandates.html": [
        "aif-title",
        "strategic-mission",
        "strategic-mission-heading",
        "five-pillars",
        "pillar-1-environmental-healing",
        "pillar-2-universal-sanctuary",
        "pillar-3-sovereign-trust",
        "pillar-4-systemic-reform",
        "pillar-5-staff-flywheel",
        "funding-mechanism",
        "legacy-access",
        "legacy-access-heading",
        "mandates-navigation",
        "mandates-footer",
    ],
    "compliance-tracker.html": [
        "tracker-header",
        "tracker-title",
        "master-ticker-section",
        "toggle-section",
        "about-acs-standard",
        "about-acs-standard-heading",
    ],
    "ledger.html": [
        "ledger-header",
        "ledger-title",
        "damages-multiplier",
        "liability-summary",
        "regulatory-mandates",
        "path-to-compliance",
        "documented-notices",
        "verified-entity-logs",
        "patent-marking",
    ],
}


def extract_ids(content):
    html_only = re.sub(r'<script\b[^>]*>.*?</script>',
                       '', content, flags=re.DOTALL | re.IGNORECASE)
    html_only = re.sub(r'<style\b[^>]*>.*?</style>',
                       '', html_only, flags=re.DOTALL | re.IGNORECASE)
    return re.findall(r'id=["\']([^"\']+)["\']', html_only)


def validate_file(file_path, required_ids):
    content = file_path.read_text(encoding="utf-8")
    ids = extract_ids(content)
    id_set = set(ids)

    issues = []

    for required_id in required_ids:
        if required_id not in id_set:
            issues.append(f"❌ MISSING: id='{required_id}'")

    duplicate_ids = sorted(
        {anchor_id for anchor_id in ids if ids.count(anchor_id) > 1})
    for duplicate_id in duplicate_ids:
        issues.append(f"⚠️  WARNING: duplicate id found: '{duplicate_id}'")

    return issues


def main():
    print("🧪 Running Anchor ID Validation\n")

    root = Path(__file__).parent
    all_issues = {}

    for file_name, required_ids in ANCHOR_REQUIREMENTS.items():
        file_path = root / file_name
        if not file_path.exists():
            all_issues[file_name] = [f"❌ MISSING FILE: {file_name}"]
            continue

        issues = validate_file(file_path, required_ids)
        if issues:
            all_issues[file_name] = issues

    if not all_issues:
        print("✅ All anchor ID checks passed!")
        return 0

    print("Issues found:\n")
    for file_name, issues in all_issues.items():
        print(f"{file_name}:")
        for issue in issues:
            print(f"  {issue}")
        print()

    critical_count = sum(
        1 for issues in all_issues.values() for issue in issues if "❌" in issue
    )
    warning_count = sum(
        1 for issues in all_issues.values() for issue in issues if "⚠️" in issue
    )

    if critical_count > 0:
        print(f"❌ {critical_count} critical issue(s)")
        return 1

    print(f"⚠️  {warning_count} warning(s) - PASSED with warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
