---
description: Respond to Greptile review comments
---

# Respond to Review

Respond to `greptile-apps[bot]` comments after evaluation.

1. **Get Context**
   - Repo and PR number.

2. **Get Comments**
   - Fetch review comments with IDs.

3. **Post Replies**
   - Loop through comments and reply based on evaluation:
     - **Incorrect:** Explain why code is correct.
     - **Context Missing:** Explain design decision.
     - **Fixed:** "Fixed in [commit]".
     - **Won't Fix:** Explain tradeoff.
   - API: `gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -X POST ...`

4. **Summary**
   - List addressed comments.
