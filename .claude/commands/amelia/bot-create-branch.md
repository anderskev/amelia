---
description: create a Git branch as hey-amelia bot
---
Create a Git branch as the hey-amelia GitHub App.

## Prerequisites

The hey-amelia GitHub App must be configured with Contents: Write permission. See `.claude/skills/hey-amelia/skill.md` for setup instructions.

## Steps

1. **Get repository context**:
   ```bash
   gh repo view --json nameWithOwner --jq '.nameWithOwner'
   ```

2. **Determine branch details**:
   - If arguments were provided: use them as the branch name or topic
   - If no arguments: ask the user for:
     - New branch name
     - Base branch (or use default)

3. **Create the branch**:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/create_branch.py \
     --repo "{owner}/{repo}" \
     --branch "{new-branch-name}"
   ```

   From a specific base branch:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/create_branch.py \
     --repo "$REPO" \
     --branch "feature/new-feature" \
     --base "develop"
   ```

   From a specific commit:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/create_branch.py \
     --repo "$REPO" \
     --branch "hotfix/urgent" \
     --sha "abc1234"
   ```

4. **Confirm**: Report the branch URL to the user.

## Branch Naming Conventions

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Urgent fixes
- `release/version` - Release branches

## Example Usage

```
/amelia:bot-create-branch
/amelia:bot-create-branch feature/add-authentication
/amelia:bot-create-branch Create a release branch from develop for v2.0
```

## Typical Workflow

1. Create branch:
   ```bash
   /amelia:bot-create-branch
   ```

2. Commit changes (use [Conventional Commits](https://www.conventionalcommits.org/) format):
   ```bash
   /amelia:bot-commit
   ```

3. Create PR (use official [PR template](../../.github/PULL_REQUEST_TEMPLATE.md)):
   ```bash
   /amelia:bot-create-pr
   ```

**Note:** All bot contributions should follow the same standards as human contributions. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for full guidelines.
