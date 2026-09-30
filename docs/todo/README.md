# TODO index

Work that is not done lives here: one document per item in `open/`, kept in `closed/` when settled.
This repo is public: no confidential project, model, well or fund names in any document.

- Never write `# TODO:` in code. Fix it now, or open a document here.
- Name the file for the problem, not the fix. The name does not change when the item closes.
- Header: `# <problem>`, `Severity: high | medium | low`, `Opened: <YYYY-MM-DD>`. No frontmatter.
- Sections as needed: what happens now, evidence, what was ruled out, blast radius, what is still
  unverified, what would unblock it, files. Target 60 lines.
- Adding a document includes adding its row below. Sort by severity, then oldest first.
- To close: move the file to `closed/`, add `Closed: <date> -- settled by: <one line>` and
  `If this was wrong, you will see: <symptom>` at the top, and move the row to `## Done`.

| Item | Opened | Severity | Summary |
|---|---|---|---|
| [direct-requests-calls-bypass-timeout-and-retry](open/direct-requests-calls-bypass-timeout-and-retry.md) | 2026-09-29 | low | 8 methods call `requests.*` directly: no timeout, no connection or status retry |

## Done

| Item | Closed | Settled by |
|---|---|---|
