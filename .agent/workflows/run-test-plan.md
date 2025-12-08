---
description: Execute a manual test plan in an isolated worktree
---

# Run Test Plan

Execute the manual test plan at `$1` in an isolated git worktree.

1. **Setup Test Worktree**
   - Create worktree from current branch: `git worktree add ...`
   - Install dependencies: `uv sync`.

2. **Parse Test Plan**
   - Extract Prerequisites, Test Cases, Verification Commands, Expected Results.

3. **Execute Tests**
   - For each test case:
     - Log ID and Name.
     - Run commands.
     - Capture output.
     - Compare with expected.
     - Record PASS/FAIL.

4. **Generate Report**
   - Create `docs/testing/test-run-{timestamp}.md`.
   - Include Summary (Pass/Fail counts) and Detailed Results.

5. **Cleanup**
   - Remove worktree: `git worktree remove ... --force`.
