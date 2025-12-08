---
description: Update an existing PR description after additional changes
---

# Update PR Description

Update PR description when additional fixes/changes are made.

1. **Find Current PR**
   - Get PR number, body, base commit.
   - `gh pr view ...`

2. **Analyze New Changes**
   - Compare since PR open: `git log {FIRST_COMMIT}..HEAD`.
   - Identify new commits and file changes.

3. **Prepare Updated Description**
   - Append "Follow-up Changes" section to original body.
   - List new changes, new commits, and reason (review feedback, bug fix, etc.).

4. **Update PR**
   - `gh pr edit --body ...`

5. **Add Comment (Optional)**
   - `gh pr comment --body ...` to notify reviewers.
