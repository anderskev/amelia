---
name: bot-commit
description: Commit files to GitHub as the hey-amelia GitHub App bot. Use when pushing commits, committing changes programmatically, or making code changes as a bot. Triggers on commit files, push changes, bot commit, hey-amelia commit.
---

# Commit Files as hey-amelia

Commit files to a GitHub repository using the hey-amelia GitHub App.

## Quick Start

```bash
# Get current repo context
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
BRANCH=$(git branch --show-current)

# Commit specific files
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "$REPO" \
  --branch "$BRANCH" \
  --message "feat(core): add new feature" \
  --files "src/feature.py,src/tests/test_feature.py"
```

## Prerequisites

The hey-amelia GitHub App must be configured with **Contents: Write** permission. See [skill.md](skill.md) for setup.

## Usage

### Step 1: Identify Files to Commit

```bash
# Get repository
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')

# Get current branch
BRANCH=$(git branch --show-current)

# List modified files
git status --short
```

### Step 2: Compose Commit Message

Use [Conventional Commits](https://www.conventionalcommits.org/) format. See [CONTRIBUTING.md](../../../CONTRIBUTING.md#commit-messages) for full guidelines.

**Format:**
```
type(scope): description

[optional body]

[optional footer: Fixes #123]
```

**Common types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`

**Common scopes:** `server`, `cli`, `dashboard`, `skills`, `commands`

### Step 3: Commit Files

```bash
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "{owner}/{repo}" \
  --branch "{branch-name}" \
  --message "type(scope): description" \
  --files "path/to/file1.py,path/to/file2.py"
```

### Creating a New Branch

Use `--create-branch` to create the branch if it doesn't exist:

```bash
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "$REPO" \
  --branch "feature/new-feature" \
  --message "feat(core): initial commit for new feature" \
  --files "src/new_feature.py" \
  --create-branch
```

### Custom Author

Override the default author information:

```bash
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "$REPO" \
  --branch "$BRANCH" \
  --message "fix(api): resolve null pointer bug" \
  --files "src/bugfix.py" \
  --author-name "Custom Bot" \
  --author-email "bot@example.com"
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--repo` | Yes | Repository in `owner/repo` format |
| `--branch` | Yes | Branch name to commit to |
| `--message` | Yes | Commit message |
| `--files` | Yes | Comma-separated list of local file paths |
| `--create-branch` | No | Create branch if it doesn't exist |
| `--author-name` | No | Commit author name (default: hey-amelia[bot]) |
| `--author-email` | No | Commit author email |

## How It Works

The script uses the GitHub Git Data API to create commits:

1. **Get branch reference** - Fetches current commit SHA
2. **Get tree** - Gets the tree SHA from the commit
3. **Create blobs** - Uploads each file as a blob (base64 encoded)
4. **Create tree** - Creates a new tree with the blobs
5. **Create commit** - Creates a commit pointing to the new tree
6. **Update ref** - Updates the branch to point to the new commit

This approach allows atomic multi-file commits.

## Examples

**Committing a single file:**
```bash
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "acme/project" \
  --branch "main" \
  --message "docs: update README" \
  --files "README.md"
```

**Committing multiple files:**
```bash
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "acme/project" \
  --branch "feature/auth" \
  --message "feat(server): implement authentication

- Add auth middleware
- Add login endpoint
- Add tests

Closes #42" \
  --files "src/auth.py,src/routes/login.py,tests/test_auth.py"
```

**Creating a feature branch with initial commit:**
```bash
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "acme/project" \
  --branch "feature/dark-mode" \
  --message "feat(dashboard): add dark mode theme" \
  --files "src/themes/dark.css,src/components/ThemeToggle.tsx" \
  --create-branch
```

## Workflow: Commit then PR

Typical workflow for making changes:

```bash
# 1. Make local changes
echo "new content" > src/feature.py

# 2. Commit to a new branch (use Conventional Commits format)
uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
  --repo "$REPO" \
  --branch "feature/my-feature" \
  --message "feat(core): add my feature" \
  --files "src/feature.py" \
  --create-branch

# 3. Create PR (see bot-create-pr.md for PR description template)
uv run python .claude/skills/hey-amelia/scripts/create_pr.py \
  --repo "$REPO" \
  --head "feature/my-feature" \
  --base "main" \
  --title "feat(core): add my feature" \
  --body "## Summary

- Add my feature

## Motivation

Closes #123."
```

## Related

- [skill.md](skill.md) - Full hey-amelia configuration and authentication
- [bot-create-pr.md](bot-create-pr.md) - Create PRs after committing
- `/amelia:bot-commit` - Command to commit files
