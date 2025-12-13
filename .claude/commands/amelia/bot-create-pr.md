---
description: create a pull request as hey-amelia bot
---
Create a pull request as the hey-amelia GitHub App.

## Prerequisites

The hey-amelia GitHub App must be configured with Contents: Write permission. See `.claude/skills/hey-amelia/skill.md` for setup instructions.

## Steps

1. **Get context**:
   ```bash
   gh repo view --json nameWithOwner --jq '.nameWithOwner'
   git branch --show-current
   ```

2. **Verify branch is pushed**:
   ```bash
   git push -u origin $(git branch --show-current)
   ```

3. **Determine PR details**:
   - If arguments were provided: use them as the PR title/description topic
   - If no arguments: ask the user for:
     - Target branch (default: main)
     - PR title
     - PR description
     - Whether to create as draft

4. **Compose the PR description**:
   - Follow the official template at `.github/PULL_REQUEST_TEMPLATE.md`
   - Use GitHub Markdown formatting
   - Include: Summary, Motivation (with issue links), Changes, Test Plan
   - Reference issues with closing keywords (Fixes #123, Closes #456)

5. **Create the PR**:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
     --repo "{owner}/{repo}" \
     --head "{source-branch}" \
     --base "{target-branch}" \
     --title "PR title" \
     --body "PR description"
   ```

   For draft PRs, add `--draft`:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
     --repo "$REPO" \
     --head "$BRANCH" \
     --base "main" \
     --title "WIP: Feature" \
     --body "Work in progress" \
     --draft
   ```

6. **Confirm**: Report the PR URL to the user.

## PR Description Template

Use the full template for significant changes:

```markdown
## Summary

- Brief description of what this PR does (1-3 bullet points)

## Motivation

Fixes #123. Why is this change needed?

## Changes

### Added
- New feature or file

### Changed
- Modified behavior

### Fixed
- Bug that was resolved

## Test Plan

- [ ] Manual testing step 1
- [ ] Manual testing step 2

## Checklist

- [ ] Tests pass locally (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check`)
- [ ] Type checking passes (`uv run mypy amelia`)
```

For small fixes, use a simplified version with Summary, Motivation, and Test Plan.

## Example Usage

```
/amelia:bot-create-pr
/amelia:bot-create-pr Add authentication feature
/amelia:bot-create-pr Create a PR for the current branch targeting develop
```
