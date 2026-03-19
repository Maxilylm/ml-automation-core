---
name: report
description: Generate reports and dashboards for ML/data science projects. Supports EDA reports, model performance reports, drift monitoring, and project status summaries.
---

# Report Generation

## When to Use
- Creating EDA summary reports
- Generating model performance reports
- Building drift monitoring dashboards
- Summarizing project status

## Report Types

| Type | Command | What It Produces |
|------|---------|-----------------|
| EDA | `/report eda [path]` | Data quality, distributions, correlations, recommendations |
| Model | `/report model` | Metrics, confusion matrix, ROC, feature importance, comparisons |
| Drift | `/report drift` | Feature drift tests, distribution shifts, recommended actions |
| Project | `/report project` | Pipeline status, code quality, PR summary, artifacts |
| Metrics | `/report metrics` | Interactive HTML dashboard with charts, live inference, and EDA visualizations |

## Workflow

1. **Identify report type** — From user request or `--type` flag
2. **Gather data** — Read agent reports, model artifacts, data files
3. **Generate visualizations** — Charts, tables, heatmaps as appropriate
4. **Write narrative** — Actionable insights, not just raw numbers
5. **Format and deliver** — Save to `reports/` directory

## Configuration

| Flag | Description | Default |
|------|-------------|---------|
| `--output` | Output file path | `reports/{type}_{timestamp}.md` |
| `--format` | Output format (md, html, json) | md |
| `--verbose` | Include detailed analysis | false |
| `--save-plots` | Save visualizations to files | true |

## Agent Coordination

- **eda-analyst** — For EDA and drift report data
- **ml-theory-advisor** — For model analysis and interpretation
- **mlops-engineer** — For project status and deployment info

## Report Bus Integration (v1.2.0)

Reads all `*_report.json` files from the report bus to populate report sections. Each report type maps to specific agent reports.

## Full Specification

See `commands/report.md` for complete output templates, example reports, and format details.
