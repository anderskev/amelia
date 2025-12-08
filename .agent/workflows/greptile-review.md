---
description: Fetch Greptile comments and evaluate
---

# Greptile Review

Fetch all comments from `greptile-apps[bot]` on the current PR and evaluate them.

1. **Get PR Context**
   - Run `gh pr view --json number,headRepository`.

2. **Fetch Comments**
   - **Issue Comments:** `gh api repos/{owner}/{repo}/issues/{number}/comments ...`
   - **Review Comments:** `gh api repos/{owner}/{repo}/pulls/{number}/comments ...`

3. **Format Feedback**
   - Combine into a single document.
   - Sections: Summary/Overview, Line-Specific Comments.
   - Filter out noise (e.g., `<details>`).

4. **Evaluate**
   - Run `eval-feedback` workflow with the formatted content.
