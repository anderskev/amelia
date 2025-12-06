---
description: generate manual test plan for PR (auto-posted by amelia-qa action)
---

# Generate Manual Test Plan

Generate a manual test plan for the current PR that will be auto-posted as a PR comment by the `amelia-qa` GitHub Action.

## Instructions

1. **Analyze the changes** in this branch compared to main:
   ```bash
   git log --oneline main..HEAD
   git diff --stat main..HEAD
   ```

2. **Identify testable functionality** - focus on:
   - New features or commands
   - Changed behavior
   - Integration points
   - Edge cases that automated tests can't cover
   - User-facing workflows

3. **Write the test plan** to `docs/testing/pr-test-plan.md` with this structure:

```markdown
# Manual Test Plan: {PR_TITLE}

## Overview
Brief description of what this PR changes and why manual testing is needed.

## Prerequisites
- [ ] Server running locally (`amelia server`)
- [ ] Clean git worktree
- [ ] Any other setup steps

## Test Cases

### 1. {Feature/Scenario Name}
**Purpose:** What this test verifies

**Steps:**
1. Do X
2. Do Y
3. Observe Z

**Expected Result:**
- Describe expected behavior

**Notes:** Any edge cases or variations to try

### 2. {Next Test Case}
...

## Regression Checks
- [ ] Existing functionality still works
- [ ] No unexpected side effects

## Notes
Any additional context for QA testers.
```

4. **Guidelines:**
   - Only include tests that require manual verification (not automated test coverage)
   - Be specific with commands and expected output
   - Include setup/teardown if needed
   - Keep it concise - focus on what's changed

5. **After PR merges:** Delete `docs/testing/pr-test-plan.md` (it's preserved in the PR comment)
