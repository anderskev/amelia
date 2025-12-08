---
description: Generate manual test plan for PR
---

# Generate Manual Test Plan

Generate a manual test plan for the current PR.

1. **Analyze Changes**
   - Run `git log --oneline main..HEAD` and `git diff --stat main..HEAD`.

2. **Identify Testable Functionality**
   - Focus on new features, changed behavior, integration points, edge cases, and user workflows.

3. **Write Test Plan**
   - Create `docs/testing/pr-test-plan.md`.
   - Includes:
     - **Overview:** What changed and why manual testing is needed.
     - **Prerequisites:** Setup commands.
     - **Test Scenarios:** TC-01, TC-02, etc. (Objective, Steps, Expected Result, Verification Commands).
     - **Test Environment Cleanup.**
     - **Test Result Template.**

4. **Review**
   - Ensure plan is specific, concise, and covers manual verification needs.
