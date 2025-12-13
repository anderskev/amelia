---
description: commit files to a branch as hey-amelia bot
---
Commit files to a GitHub repository as the hey-amelia GitHub App.

## Prerequisites

The hey-amelia GitHub App must be configured with Contents: Write permission. See `.claude/skills/hey-amelia/skill.md` for setup instructions.

## Steps

1. **Get context**:
   ```bash
   gh repo view --json nameWithOwner --jq '.nameWithOwner'
   git branch --show-current
   ```

2. **Identify files to commit**:
   ```bash
   git status --short
   ```

3. **Determine commit details**:
   - If arguments were provided: use them as the commit message topic
   - If no arguments: ask the user for:
     - Which files to commit
     - Commit message
     - Whether to create a new branch

4. **Compose commit message** using [Conventional Commits](https://www.conventionalcommits.org/) format:

   **Format:** `type(scope): description`

   **Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`

   **Scopes:** `server`, `cli`, `dashboard`, `skills`, `commands`

   See [CONTRIBUTING.md](../../CONTRIBUTING.md#commit-messages) for full guidelines.

5. **Commit the files**:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
     --repo "{owner}/{repo}" \
     --branch "{branch-name}" \
     --message "type(scope): description" \
     --files "path/to/file1.py,path/to/file2.py"
   ```

   To create a new branch:
   ```bash
   uv run python .claude/skills/hey-amelia/scripts/commit_files.py \
     --repo "$REPO" \
     --branch "feature/new-feature" \
     --message "feat(core): initial commit" \
     --files "src/feature.py" \
     --create-branch
   ```

6. **Confirm**: Report the commit SHA and URL to the user.

## Commit Message Guidelines

- Use [Conventional Commits](https://www.conventionalcommits.org/) format: `type(scope): description`
- Use imperative mood: "add feature" not "added feature"
- Keep first line under 72 characters
- Reference issues: `Fixes #123` or `Closes #456`
- Mark breaking changes with `!` after type/scope

## Example Usage

```
/amelia:bot-commit
/amelia:bot-commit Commit the changes to fix the auth bug
/amelia:bot-commit Create a new branch and commit src/feature.py
```

## Typical Workflow

1. Commit files to a branch:
   ```bash
   /amelia:bot-commit
   ```

2. Then create a PR:
   ```bash
   /amelia:bot-create-pr
   ```
