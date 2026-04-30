# Pull Request

## Summary

- What changed:
- Why:

## Validation

- [ ] Ran `python test/validate_compliance_tracker.py`
- [ ] Ran `python test/validate_mandates.py`
- [ ] Ran `python test/validate_anchors.py`

## UI Change Gate

- [ ] No UI-facing files changed (`.html`, `.css`, `.scss`, `.sass`, `.jsx`, `.tsx`)
- [ ] UI-facing files changed and screenshot evidence is included below

CI also runs `UI Screenshot Diff` and posts a PR comment summary comparing base vs head screenshots.

## UI Change Evidence (required when UI files changed)

If UI files changed, include at least one image under **BEFORE** and one image under **AFTER**.
Use Markdown images, for example: `![before](https://...)`

If there are no visual changes, note that explicitly under **Notes**.

### BEFORE

<!-- Add one or more BEFORE screenshots here -->

### AFTER

<!-- Add one or more AFTER screenshots here -->

### Optional per-file mapping

| File              | BEFORE     | AFTER      |
| ----------------- | ---------- | ---------- |
| path/to/file.html | image/link | image/link |

## Notes

- Risks / follow-ups:
