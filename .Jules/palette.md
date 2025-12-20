# Palette's Journal

## 2025-12-20 - Focus Management for Dynamic Forms
**Learning:** When a form or input is dynamically revealed (like rejection feedback), users expect immediate focus. Without `autoFocus`, keyboard users are left stranded on the trigger or lost in the document.
**Action:** Always apply `autoFocus` to the primary input when a container is conditionally rendered or revealed.
