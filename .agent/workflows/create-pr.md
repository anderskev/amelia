---
description: Create a pull request with standardized description template
---

# Create Pull Request

Create a pull request with a well-structured description based on the branch changes.

1. **Gather Context**
   - Verify branch: `git branch --show-current`.
   - Get history: `git log --oneline main..HEAD`.
   - Get details: `git log --format="### %s%n%n%b" main..HEAD`.
   - Get stats: `git diff --stat main..HEAD`.
   - Get diff: `git diff main..HEAD`.

2. **Analyze Changes**
   - **What:** Feature, fix, refactor, etc.
   - **Why:** Motivation.
   - **Impact:** Breaking changes, migrations.
   - **Testing:** Evidence of verification.

3. **Check Related Issues**
   - Find references in commits (`fixes #123`) or branch name.

4. **Generate PR Description**
   - Create title: `<type>(<scope>): <description>`
   - Create body using template:
     - Summary
     - Changes (Added, Changed, Fixed, Removed)
     - Motivation
     - Testing (Unit, Integration, Manual)
     - Breaking Changes (if any)
     - Related Issues
     - Checklist

5. **Create PR**
   - Run `gh pr create` with the generated title and body.
   - Display PR URL and suggest reviewers.
