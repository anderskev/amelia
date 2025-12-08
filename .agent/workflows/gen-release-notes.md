---
description: Generate release notes for changes since a given tag
---

# Release Notes Generator

Generate professional release notes following the Keep a Changelog standard.

**Input:** `$ARGUMENTS` (Previous tag, e.g., `v0.0.1`)

1. **Gather Changes**
   - Store previous tag: `PREV_TAG="$ARGUMENTS"`.
   - Verify tag: `git tag -l "$PREV_TAG"`.
   - List commits: `git log ${PREV_TAG}..HEAD --pretty=format:"%h %s" --no-merges`.
   - Diff stats: `git diff ${PREV_TAG}..HEAD --stat`.
   - Changed files: `git diff ${PREV_TAG}..HEAD --name-only | sort | uniq`.
   - (Optional) Get merged PRs if `gh` CLI is available.

2. **Analyze and Categorize**
   - Group changes into:
     - **Added:** New features, public APIs.
     - **Changed:** Modified behavior, performance, user-facing updates.
     - **Deprecated:** Features marked for removal.
     - **Removed:** Deleted features.
     - **Fixed:** Bug fixes.
     - **Security:** Vulnerability patches.
   - Exclude internal refactors, test-only changes, CI/CD unless user-facing.

3. **Determine Version Number**
   - Suggest next version (MAJOR, MINOR, PATCH) based on SemVer.

4. **Write Release Notes**
   - Format:
     ```markdown
     ## [VERSION] - YYYY-MM-DD
     ### Added
     - **scope:** Description ([#PR](link))
     ...
     ```
   - Use imperative verbs.
   - Include scope prefixes (`server`, `cli`, etc.).
   - Highlight **Breaking** changes with migration notes.

5. **Update CHANGELOG.md**
   - Insert new version entry after `[Unreleased]`.
   - Create file if missing.
   - Update version comparison links.

6. **Output Summary**
   - Show suggested version, summary of changes, and confirmation of update.
