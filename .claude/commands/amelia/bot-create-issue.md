---
description: create a GitHub issue as hey-amelia bot
---
Create a GitHub issue as the hey-amelia GitHub App.

## Prerequisites

The hey-amelia GitHub App must be configured. See `.claude/skills/hey-amelia/skill.md` for setup instructions.

## Steps

1. **Get repository context**:
   ```bash
   gh repo view --json nameWithOwner --jq '.nameWithOwner'
   ```

2. **Get available labels** (optional):
   ```bash
   gh label list
   ```

3. **Determine issue details**:
   - If arguments were provided: use them as the issue topic
   - If no arguments: ask the user for:
     - Issue title
     - Issue description
     - Labels (optional)
     - Assignees (optional)

4. **Compose the issue**:
   - Follow official templates at `.github/ISSUE_TEMPLATE/`
   - Use GitHub Markdown formatting
   - For bugs: include steps to reproduce, affected area
   - For features: include motivation and proposed solution

5. **Apply labels** from [CONTRIBUTING.md](../../CONTRIBUTING.md#labels):
   - Type: `bug`, `enhancement`, `breaking-change`, `docs`
   - Priority: `critical`, `high`, `low`
   - Status: `needs-triage` (always add for new issues)
   - Area: `area:core`, `area:agents`, `area:dashboard`, `area:cli`, `area:server`

6. **Create the issue**:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/create_issue.py \
     --repo "{owner}/{repo}" \
     --title "Issue title" \
     --body "Issue description"
   ```

   With labels and assignees:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/create_issue.py \
     --repo "$REPO" \
     --title "Bug: Description" \
     --body "Details here" \
     --labels "bug,area:server,high,needs-triage" \
     --assignees "username"
   ```

7. **Confirm**: Report the issue URL to the user.

## Issue Templates

**Bug report:**
```markdown
## Description

Clear description of the bug.

## Steps to Reproduce

1. Step one
2. Step two

## Expected Behavior

What should happen.

## Actual Behavior

What actually happens.
```

**Feature request:**
```markdown
## Summary

Brief description of the feature.

## Motivation

Why this feature is needed.

## Proposed Solution

How it could be implemented.
```

## Example Usage

```
/amelia:bot-create-issue
/amelia:bot-create-issue Bug: Login fails with empty password
/amelia:bot-create-issue Create a follow-up issue for tech debt from PR #42
```
