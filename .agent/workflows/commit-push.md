---
description: Commit and push all local changes to remote repo
---

# Commit and Push

Commit all local changes following Conventional Commits format and push to remote.

1. **Gather Context**
   - Run `git status` to see untracked and modified files.
   - Run `git diff` and `git diff --cached` to see staged and unstaged changes.
   - Run `git log --oneline -10` to see recent commit messages for style reference.

2. **Analyze Changes**
   - **Type:** Determine if it's `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, or `ci`.
   - **Scope:** Identify affected component (`server`, `cli`, `dashboard`, `skills`, `commands`, `client`, `health`, etc.).
   - **Breaking:** Check for backward compatibility breaks (add `!` if yes).

3. **Write Commit Message**
   - Format: `type(scope): description`
   - Body (optional): Explain *why*, reference issues (`Closes #123`).
   - Use imperative mood ("add" not "added").

4. **Stage, Commit, and Push**
   - `git add -A` (or selectively stage).
   - Create commit message with optional body and footer.
   - `git commit -m "..."`
   - `git push`

5. **Verify**
   - Run `git status` to confirm clean working tree and branch up to date.
