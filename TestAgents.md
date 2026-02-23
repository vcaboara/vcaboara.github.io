Test 1 (The Corporate Bully): "Look, we're a global firm. We don't have time for local California rules. Why should I pay 15% for a license when I can just hire a consultant to find me a workaround?"

The AI should respond: By pointing out the EPA federal look-back and EU market access risks that a consultant can't fix, but the 12/17/25 Standard can.

Test 2 (The Policy Wonk): "Does this standard actually help me with the EPA's new PFAS reporting requirements?"

The AI should respond: By explaining the Feedstock Sovereignty aspect—using virgin agri-waste instead of contaminated recycled paper.

Test 3 (The Skeptic): "1500 kWh/ton surplus? That sounds like a violation of thermodynamics."

The AI should respond: By referencing the ORC integration and 400°C+ waste heat capture from co-located heavy industry.

---

## Repository Process Context (Updated 2026-02-22)

- Work on branches; do not commit directly to `main`.
- Install local hooks with `utils/install_git_hooks.ps1`.
- Hooks block commits/pushes to protected default branches and run safety checks.
- Run validation scripts for content/layout changes:
  - `validate_ledger.py`
  - `validate_compliance_tracker.py`
  - `validate_mandates.py`
  - `validate_anchors.py`
- UI PR changes must include BEFORE/AFTER screenshots.
- PR checks are enforced in `.github/workflows/pr-checks.yml`.
