---
description: create a pull request with standardized description template
---

# Create Pull Request

Create a pull request with a well-structured description based on the branch changes.

## Instructions

### 1. Gather Context

First, collect information about the changes:

```bash
# Get current branch and verify it's not main
git branch --show-current

# Get commit history for this branch
git log --oneline main..HEAD

# Get detailed commit messages for context
git log --format="### %s%n%n%b" main..HEAD

# Get file change statistics
git diff --stat main..HEAD

# Get the actual diff for understanding changes
git diff main..HEAD
```

### 2. Analyze the Changes

Based on the gathered information, determine:

- **What changed**: Categorize changes (features, fixes, refactors, docs, tests)
- **Why it changed**: Infer motivation from commit messages and code changes
- **Impact**: Breaking changes, new dependencies, migrations needed
- **Testing**: What tests were added/modified, how to verify manually

### 3. Check for Related Issues

Look for issue references:
- In commit messages (e.g., "fixes #123", "closes #456")
- In branch name (e.g., `fix/issue-123-description`)
- In code comments or TODOs addressed

### 4. Generate PR Description

Create the PR using this template structure:

```bash
gh pr create --title "<type>(<scope>): <description>" --body "$(cat <<'EOF'
## Summary

<1-3 sentence overview of what this PR does and why>

## Changes

<Categorized bullet list of changes>

### Added
- <new features or capabilities>

### Changed
- <modifications to existing functionality>

### Fixed
- <bug fixes>

### Removed
- <deprecated or removed functionality>

## Motivation

<Why were these changes needed? What problem does this solve?>

## Testing

<How was this tested?>

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

### Manual Testing Steps

<If applicable, steps to manually verify the changes>

## Breaking Changes

<If any, describe what breaks and migration path. Remove section if none.>

## Related Issues

<Link to related issues. Remove section if none.>

- Closes #<issue_number>
- Related to #<issue_number>

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check`)
- [ ] Type checking passes (`uv run mypy amelia`)
- [ ] Documentation updated (if needed)

---

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 5. Title Format

Use conventional commit format for the PR title:
- `feat(scope): add new feature`
- `fix(scope): correct bug behavior`
- `refactor(scope): restructure without behavior change`
- `docs(scope): update documentation`
- `test(scope): add or modify tests`
- `chore(scope): maintenance tasks`

### 6. Apply Labels

After creating the PR, apply appropriate labels based on the changes. Use `gh pr edit <number> --add-label <label>`.

#### Type Labels (pick one)

| Label | When to Use |
|-------|-------------|
| `enhancement` | New features, capabilities, or improvements |
| `bug` | Bug fixes |
| `docs` | Documentation-only changes |
| `breaking-change` | **User-facing** breaking changes requiring migration (not internal refactors) |

#### Area Labels (pick all that apply)

Determine areas by checking which directories have changes:

| Directory | Label |
|-----------|-------|
| `amelia/core/`, `amelia/drivers/` | `area:core` |
| `amelia/agents/` | `area:agents` |
| `amelia/server/` | `area:server` |
| `amelia/main.py`, CLI-related | `area:cli` |
| `dashboard/` | `area:dashboard` |

```bash
# Example: Apply labels for a feature touching core and agents
gh pr edit <PR_NUMBER> --add-label enhancement --add-label area:core --add-label area:agents
```

#### Breaking Change Criteria

Only apply `breaking-change` for **user-facing** changes that require users to modify their:
- Configuration files
- CLI invocations
- API integrations

Do NOT apply for internal refactors (driver interfaces, internal state changes) unless they affect external consumers.

### 7. After Creation

After creating the PR:
1. Display the PR URL with applied labels
2. Suggest adding reviewers if appropriate
3. Note if any CI checks need to pass

## Guidelines

**DO:**
- Be specific about what changed and why
- Include testing evidence
- Link related issues
- Note breaking changes prominently
- Remove empty optional sections
- Apply type label (enhancement/bug/docs) and all relevant area labels
- Reserve `breaking-change` for user-facing changes only

**DON'T:**
- Include irrelevant commits (keep PR focused)
- Leave placeholder text in the description
- Skip the testing section
- Create PRs without running local checks first
- Apply `breaking-change` for internal API refactors

## Example Output

```
Created PR #42: fix(health): wire websocket_connections to actual count
URL: https://github.com/anderskev/amelia/pull/42
Labels: bug, area:server

Suggested reviewers: @teammate1, @teammate2
```
