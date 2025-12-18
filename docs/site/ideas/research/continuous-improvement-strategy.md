# Continuous Improvement Strategy

> **Created by:** hey-amelia bot with Claude Opus 4.5 and Gemini 3 Pro with Deep Research

A strategic framework for building a quality flywheel that compounds agent performance over time.

## Executive Summary

This strategy transforms Amelia from a static system requiring manual tuning into a learning system that improves through structured feedback. The approach applies reinforcement learning principles at the prompt layer—generating variants, evaluating against benchmarks, selecting top performers, and iterating—creating compounding quality gains without model fine-tuning.

**Key insight**: We cannot fine-tune the underlying LLM, but we can apply the same optimization principles that make systems like Gemini effective. Clear reward signals (benchmark results) enable systematic improvement at the prompt and configuration layer.

**Business value**: Evidence-based iteration replaces intuition-based prompt engineering. Regressions are detected before deployment. Quality improvements compound rather than eroding with model updates.

---

## Strategic Context

### The Problem with Static Agents

Today's agent behavior is fixed at deployment. Performance improvements require manual prompt engineering—a process that is:

- **Unmeasurable**: Changes are evaluated anecdotally, not objectively
- **Risky**: Improvements in one area often cause regressions elsewhere
- **Non-compounding**: Knowledge lives in engineers' heads, not in systems

### The Opportunity

Benchmark-driven evaluation combined with systematic prompt optimization creates a quality flywheel:

```
Benchmark reveals weakness → Targeted improvement → Verification → New baseline → Repeat
```

Each cycle compounds. The system gets measurably better over time rather than degrading with model updates and requirement drift.

---

## Technical Approach

### Core Principles from Reinforcement Learning Research

Gemini research demonstrates that RL techniques improve reasoning and code generation through systematic feedback loops. Four principles translate directly to prompt optimization:

| Principle | Gemini Application | Amelia Application |
|-----------|-------------------|-------------------|
| **Multi-Agent Selection** | Multiple agents propose solutions; best selected based on test results | Generate prompt variants; benchmark each; select top performers |
| **Evolutionary Self-Play** | Filter candidates through evolutionary loop; fine-tune on winners | Rejection sampling with benchmark-driven selection |
| **Extended Reasoning** | Deep Think explores hypotheses before deciding | Prompts that encourage multi-perspective reasoning |
| **Feedback-Driven Learning** | Models learn from execution results | Benchmarks provide execution feedback; iteration applies learning |

### Benchmark Architecture

A benchmark framework requires four components:

1. **Test Cases**: Curated dataset with known quality characteristics, spanning positive and negative examples
2. **Runner**: Executes agents against test cases with consistent configuration; captures outcomes, token usage, latency
3. **Evaluator**: Computes metrics—accuracy, recall, false positive rate, severity correlation
4. **Reporter**: Stores historical results; generates trend reports; detects regressions

### Dual-Test Criteria

Each benchmark case carries two verification requirements (borrowed from SWE-bench methodology):

- **FAIL_TO_PASS**: The primary success criterion—did the agent detect what it should?
- **PASS_TO_PASS**: The regression prevention criterion—did it avoid breaking what was working?

Both must pass. This prevents solutions that fix one problem while breaking others.

### Avoiding Overfitting

Benchmarks are proxies for production quality, not quality itself. Safeguards include:

- **Hold-out sets**: Reserved cases never used during optimization reveal whether improvements generalize
- **Dynamic updates**: Rotate test cases; add cases from production failures
- **Multiple metrics with constraints**: Prevent gaming any single metric (Goodhart's Law)

---

## Implementation Phases

### Phase 1: Reviewer Agent Foundation

The Reviewer is the ideal starting point:

- **Clean reward signal**: Binary output (approved/rejected) provides unambiguous feedback
- **Natural iteration cycles**: Review-fix loops generate structured training data
- **Immediate value**: Better code review quality while building the improvement system

**Deliverables:**
- Benchmark framework (test cases, runner, evaluator, reporter)
- Initial Reviewer test suite with dual-test criteria
- Metrics dashboard with per-category, per-difficulty breakdowns
- Documented iteration workflow for prompt optimization

### Phase 2: Full Workflow Extension

Extending to Architect and Developer agents presents additional challenges:

| Agent | Challenge | Approach |
|-------|-----------|----------|
| **Architect** | Plan quality only apparent during execution | Evaluate plans through downstream execution; track plan-to-execution correlation |
| **Developer** | Success depends on tests, review, production behavior | Adapt SWE-bench methodology; use review iterations as quality signal |

**Additional capabilities:**
- Multi-agent selection for high-stakes tasks (spawn parallel configurations; select best)
- Prompt template externalization for A/B testing at scale
- Token and cost optimization metrics alongside quality metrics

---

## Metrics Framework

### Why Granularity Matters

Aggregate metrics mask important variation. An 80% overall accuracy might hide 95% on easy cases and 40% on hard cases—where production value often concentrates.

### Recommended Metric Dimensions

| Dimension | Purpose |
|-----------|---------|
| **Per-category** | Security, performance, correctness—where does the agent excel vs struggle? |
| **Per-difficulty** | Easy, medium, hard—hard case performance often matters most |
| **Per-configuration** | Which agent configurations perform best for which task types? |
| **Per-iteration** | Does performance degrade across review-fix cycles? |

Aggregate metrics tell you something is wrong; granular metrics tell you what to fix.

---

## Success Criteria

### Short-term (Phase 1)

- Baseline Reviewer benchmark established with 50+ test cases
- Metrics dashboard operational with historical trending
- At least one prompt improvement cycle completed with measured gains
- Regression detection in place before production deployment

### Medium-term (Phase 2)

- Developer and Architect agents under benchmark coverage
- Multi-agent selection available for high-stakes tasks
- Token efficiency metrics tracking cost alongside quality
- Prompt templates externalized for configuration-based A/B testing

### Long-term

- Quality flywheel operational: systematic improvement cycles running regularly
- Production feedback loop: real failures inform benchmark updates
- Model update resilience: regressions detected and addressed within days, not weeks

---

## Risk Considerations

| Risk | Mitigation |
|------|------------|
| **Overfitting to benchmarks** | Hold-out sets; production feedback; metric diversity |
| **High benchmark maintenance cost** | Start small; grow from production failures; automate where possible |
| **Measurement without action** | Tie metrics to actionable improvement workflow; avoid vanity dashboards |
| **Token cost of experimentation** | Run variants on subsets; prioritize high-leverage improvements |

---

## Research References

**Benchmarking methodology:**
- SWE-bench dual-test criteria for measuring code agent performance
- Harbor framework patterns for container-based agent evaluation

**Reinforcement learning for code:**
- [Google DeepMind Gemini](https://deepmind.google/models/gemini/) — RL for reasoning and code generation
- [AlphaCode at ICPC](https://deepmind.google/discover/blog/gemini-achieves-gold-level-performance-at-the-international-collegiate-programming-contest-world-finals/) — Evolutionary self-play for program synthesis
- [Gemini 2.5 Technical Report](https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf) — Multi-step RL for tool use

**Agent evaluation research:**
- Reflexion pattern (91% vs 80% on coding tasks) informing self-review cycles
- Granularity gaps in aggregate metrics driving per-agent, per-step measurement

---

## Summary

This strategy establishes a foundation for continuous agent improvement through:

1. **Benchmark infrastructure** that provides objective measurement
2. **RL-inspired optimization** applied at the prompt layer without model fine-tuning
3. **Granular metrics** that direct improvement efforts precisely
4. **Safeguards** against overfitting and regression

The end state is a quality flywheel where each iteration compounds—an agent system that gets measurably better over time rather than requiring constant manual intervention.
