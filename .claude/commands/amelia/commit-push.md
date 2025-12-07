---
description: commit and push all local changes to remote repo
---

# Commit and Push

Commit all local changes following Conventional Commits format and push to remote.

## Step 1: Gather Context

Run these commands in parallel to understand the changes:
- git status (see all untracked and modified files)
- git diff (see unstaged changes)
- git diff --cached (see staged changes)
- git log --oneline -10 (see recent commit messages for style reference)

## Step 2: Analyze Changes

Review the changes and determine:

**Type** - What kind of change is this?
- feat: New feature or capability
- fix: Bug fix
- docs: Documentation only
- refactor: Code restructure without behavior change
- test: Adding or updating tests
- chore: Maintenance, dependency updates
- perf: Performance improvement
- ci: CI/CD changes

**Scope** - Which component is affected?
- server: Backend FastAPI server
- cli: Command-line interface
- dashboard: React frontend
- skills: Claude Code skills
- commands: Slash commands
- client: API client
- health: Health check endpoints
- Omit scope for cross-cutting changes

**Breaking** - Does this break backward compatibility? If yes, add an exclamation mark after scope (e.g., feat!(api): ...).

## Step 3: Write Commit Message

Format: type(scope): description

The first line should be imperative mood ("add feature" not "added feature") and under 72 characters.

Optionally add a body explaining *why* (the diff shows *what*) and footer with issue references (Closes #123 or Fixes #456).

## Step 4: Stage, Commit, and Push

1. Stage all changes with: git add -A
2. Commit using a HEREDOC for multi-line messages, including the Claude Code attribution footer
3. Push to remote with: git push

The commit message should end with:

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

## Step 5: Verify

After pushing, run git status to confirm the working tree is clean and the branch is up to date with remote.
