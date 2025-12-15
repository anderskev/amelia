---
title: Example Artifacts
description: Real examples of design documents, plans, and reviews produced by Amelia
---

# Example Artifacts

Amelia produces structured artifacts throughout the development lifecycle. These examples showcase the format and depth of each artifact type.

## Artifact Types

<div class="artifact-cards">

### Design Documents

Technical specifications and architectural decisions that define how a feature should be built.

[View Example &rarr;](/amelia/guide/artifacts/design-example)

### Implementation Plans

Step-by-step execution plans with batched tasks, risk assessment, and checkpoints.

[View Example &rarr;](/amelia/guide/artifacts/plan-example)

### Code Reviews

Comprehensive review feedback covering correctness, architecture, security, and maintainability.

[View Example &rarr;](/amelia/guide/artifacts/review-example)

</div>

## How Artifacts Are Used

```
Issue → Architect (design) → Plan Approval → Developer (plan) → Reviewer (review) → Done
```

1. **Design**: The Architect agent analyzes requirements and produces a design document
2. **Plan**: The design is translated into an executable plan with batched steps
3. **Review**: The Reviewer evaluates changes against the design and coding standards

## Current Status

These artifacts are currently produced manually using hey-amelia. Automated artifact generation is on the [roadmap](/amelia/reference/roadmap).

<style>
.artifact-cards {
  display: grid;
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.artifact-cards h3 {
  margin-top: 0;
  color: var(--vp-c-brand-1);
}

.artifact-cards p {
  margin-bottom: 0.5rem;
}

.artifact-cards a {
  font-weight: 500;
}
</style>
