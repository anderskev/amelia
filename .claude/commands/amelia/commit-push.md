---
description: commit and push all local changes to remote repo
---

# Commit and Push

Commit all local changes following Conventional Commits format and push to remote.

## Step 1: Gather Context

Run these commands in parallel to understand the changes:

```bash
# See all untracked and modified files
git status

# See staged and unstaged changes
git diff
git diff --cached

# See recent commit messages for style reference
git log --oneline -10
```

## Step 2: Analyze Changes

Review the changes and determine:
- **Type**: What kind of change is this?
  - `feat` - New feature or capability
  - `fix` - Bug fix
  - `docs` - Documentation only
  - `refactor` - Code restructure without behavior change
  - `test` - Adding or updating tests
  - `chore` - Maintenance, dependency updates
  - `perf` - Performance improvement
  - `ci` - CI/CD changes

- **Scope**: Which component is affected?
  - `server` - Backend FastAPI server
  - `cli` - Command-line interface
  - `dashboard` - React frontend
  - `skills` - Claude Code skills
  - `commands` - Slash commands
  - `client` - API client
  - `health` - Health check endpoints
  - *(omit scope for cross-cutting changes)*

- **Breaking**: Does this break backward compatibility? If yes, add **!** after scope.

## Step 3: Write Commit Message

Format:
```
type(scope): description

[optional body explaining why, not what]

[optional footer with issue references]
```

Rules:
- Use imperative mood: "add feature" not "added feature"
- Keep first line under 72 characters
- Focus on *why* in the body, the diff shows *what*
- Reference issues: `Closes #123` or `Fixes #456`

## Step 4: Stage, Commit, and Push

```bash
# Stage all changes (or selectively stage)
git add -A

# Commit with message (use HEREDOC for multi-line)
git commit -m "$(cat <<'EOF'
type(scope): description

Optional body explaining the motivation.

Closes #123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to remote
git push
```

## Examples

```bash
# Simple feature
git commit -m "feat(cli): add --verbose flag to start command"

# Bug fix with body
git commit -m "$(cat <<'EOF'
fix(server): handle timeout when LLM response exceeds limit

The previous implementation did not account for streaming responses
that exceed the configured timeout window.

Fixes #42

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Breaking change
git commit -m "$(cat <<'EOF'
feat!(api): change workflow status response format

BREAKING CHANGE: The `status` field is now an object with `state` and
`message` properties instead of a plain string.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Step 5: Verify

After pushing, run `git status` to confirm the working tree is clean and the branch is up to date with remote.
