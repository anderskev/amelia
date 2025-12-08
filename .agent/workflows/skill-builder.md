---
description: Create and validate Claude Code skills
---

# Skill Builder

Create, validate, and refine Claude Code skills.

1. **Gather Requirements**
   - **Required:** Capability, Triggers, Domain Knowledge.
   - **Optional:** Utils, Tool restrictions, Key files.

2. **Design Structure**
   - **Simple:** Single `SKILL.md`.
   - **Multi-file:** `SKILL.md`, `reference.md`, `scripts/`.

3. **Write SKILL.md**
   - **Frontmatter:** `name` (lowercase-hyphen), `description` (3rd person + triggers).
   - **Body:** Quick Start, Instructions, Workflows, Examples.

4. **Apply Best Practices**
   - Conciseness.
   - Degrees of Freedom (match specificity to ease).
   - Feedback Loops.
   - Checklists.
   - Examples.
   - Progressive Disclosure.

5. **Validate**
   - Check against Validation Checklist (Quality, Technical, Tools).

6. **Test**
   - Place in `.claude/skills/`.
   - Restart Claude Code.
   - Test with natural language triggers.
   - Verify navigation.
