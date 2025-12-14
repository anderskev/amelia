---
name: bot-create-pr
description: Create pull requests as the hey-amelia GitHub App bot. Use when opening PRs, creating pull requests programmatically, or submitting changes for review as a bot. Triggers on create PR, open PR, bot PR, hey-amelia PR.
---

# Create Pull Requests as hey-amelia

Create pull requests using the hey-amelia GitHub App.

## Quick Start

```bash
# Get current repo context
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
BRANCH=$(git branch --show-current)

# Create a PR
uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
  --repo "$REPO" \
  --head "$BRANCH" \
  --base "main" \
  --title "Your PR title" \
  --body "Description of changes"
```

## Prerequisites

The hey-amelia GitHub App must be configured. See [skill.md](skill.md) for setup.

## Usage

### Step 1: Get Context

```bash
# Get repository
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')

# Get current branch
BRANCH=$(git branch --show-current)

# Verify branch is pushed
git push -u origin "$BRANCH"
```

### Step 2: Compose PR Description

Use the official PR template from `.github/PULL_REQUEST_TEMPLATE.md`. Format PR descriptions using GitHub Markdown.

**Full template (recommended for significant changes):**
```markdown
## Summary

<!-- 1-3 bullet points describing what this PR does -->
- Brief description of what this PR does

## Motivation

<!-- Why is this change needed? Link issues with closing keywords -->
Fixes #123.

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

**Simplified template (for small fixes):**
```markdown
## Summary

- One-line description

## Motivation

Fixes #123.

## Test Plan

- [ ] Verified the fix locally
```

### Step 3: Create PR

```bash
uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
  --repo "{owner}/{repo}" \
  --head "{source-branch}" \
  --base "{target-branch}" \
  --title "PR title" \
  --body "PR description"
```

For multi-line descriptions, use a heredoc:

```bash
uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
  --repo "$REPO" \
  --head "$BRANCH" \
  --base "main" \
  --title "Add new feature" \
  --body "$(cat <<'EOF'
## Summary

Your multi-line description here.

## Changes

- Point 1
- Point 2
EOF
)"
```

### Creating Draft PRs

Add the `--draft` flag to create a draft PR:

```bash
uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
  --repo "$REPO" \
  --head "$BRANCH" \
  --base "main" \
  --title "WIP: Feature in progress" \
  --body "Work in progress" \
  --draft
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--repo` | Yes | Repository in `owner/repo` format |
| `--head` | Yes | Source branch (with your changes) |
| `--base` | Yes | Target branch (to merge into) |
| `--title` | Yes | PR title |
| `--body` | Yes | PR description |
| `--draft` | No | Create as draft PR |

## Examples

**Creating a feature PR:**
```bash
uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
  --repo "acme/project" \
  --head "feature/add-auth" \
  --base "main" \
  --title "feat(auth): add user authentication" \
  --body "$(cat <<'EOF'
## Summary

- Implements JWT-based authentication for API endpoints

## Motivation

Closes #123. Users need secure authentication to access protected resources.

## Changes

### Added
- Auth middleware for JWT validation
- Login/logout endpoints
- User session management

## Test Plan

- [ ] Test login with valid credentials
- [ ] Test login with invalid credentials
- [ ] Test protected endpoint access

## Checklist

- [ ] Tests pass locally
- [ ] Linting passes
- [ ] Type checking passes
EOF
)"
```

**Creating a hotfix PR:**
```bash
uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
  --repo "acme/project" \
  --head "hotfix/fix-crash" \
  --base "main" \
  --title "fix(checkout): handle null cart in checkout" \
  --body "$(cat <<'EOF'
## Summary

- Adds null check before accessing user cart

## Motivation

Fixes #456.

## Test Plan

- [ ] Verified checkout works with empty cart
EOF
)"
```

## Related

- [skill.md](skill.md) - Full hey-amelia configuration and authentication
- [bot-commit.md](bot-commit.md) - Commit files before creating PR
- `/amelia:bot-create-pr` - Command to create PRs
