---
name: team-analyze
description: Run a quick analysis workflow on any dataset. Performs EDA, quality review, and provides recommendations. Works with any tabular data - CSV, Excel, database exports, etc.
---

# Team Analyze

## When to Use
- Quick dataset analysis with automated quality review
- Getting recommendations for data preparation and modeling
- Running a coordinated analysis with multiple specialist agents

## Workflow

1. Data validation and loading
2. EDA (parallel with ML theory review and feature analysis)
3. Quality review and leakage detection
4. Feature engineering recommendations
5. Summary with actionable next steps

## Report Bus Integration (v1.2.0)

All agents write structured reports to the shared report bus. After EDA completes, spawn ml-theory-advisor and feature-engineering-analyst in parallel — they both read the EDA report independently.

Use `ml_utils.get_workflow_status()` after all agents complete to display a unified summary.

## Reflection Gate (v1.2.1)

After parallel analysis completes, a reflection gate validates feature engineering output before the summary report. The ml-theory-advisor evaluates the strategy and either approves or requests revisions (max configurable iterations, default 2). Set `--max-reflect 0` to skip.

## MLOps Registry (v1.3.0)

During analysis, eda-analyst generates a data fingerprint and feature-engineering-analyst registers features. Use `/registry` to inspect stored artifacts.

## Self-Check (v1.4.0)

After each analysis stage, validate outputs with `validate_stage_output()`. Load lessons from prior runs with `ml_utils.load_lessons()` to inform agent context.

## Full Specification

See `commands/team-analyze.md` for the complete analysis workflow, parallel execution configuration, and reflection gate details.
