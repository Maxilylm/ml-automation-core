---
name: registry
description: Inspect MLOps registries — models, features, experiments, and data versions
---

# Registry

## When to Use
- Inspecting what models, features, and experiments have been tracked
- Checking model lineage from data to deployment
- Comparing experiment runs and model versions
- Verifying registry completeness after a pipeline run

## What It Shows

- **Model Registry**: Trained models with status (champion/challenger/archived), metrics, and lineage
- **Feature Store**: Engineered features with transformations, statistics, and leakage risk
- **Experiment Tracking**: Training runs with hyperparameters, metrics, and rationale
- **Data Versioning**: Dataset fingerprints for reproducibility

## Workflow

1. **Scan registry directories** — Check all platform dirs for registry files
2. **Parse and validate** — Load JSON registries, handle missing/empty gracefully
3. **Display tables** — Show structured tables per registry type
4. **Lineage tracing** — If `--lineage` requested, trace from data version → features → experiment → model
5. **Summary** — Highlight champion model, latest experiment, any gaps

## Subcommands

| Subcommand | What It Shows |
|------------|--------------|
| `/registry models` | Model versions, metrics, champion status |
| `/registry features` | Feature store entries with transformations |
| `/registry experiments` | Training runs with hyperparameters and metrics |
| `/registry data` | Data version fingerprints |
| `/registry lineage` | End-to-end traceability |
| `/registry summary` | Overview of all registries |

## Flags

| Flag | Description |
|------|-------------|
| `--champion` | Show only the champion model |
| `--domain <type>` | Filter by task type (classification, regression, etc.) |
| `--lineage` | Show full data-to-model lineage |

## Registry Locations

Registries are stored in platform-specific directories:
- `.claude/mlops/` (Claude Code)
- `.cursor/mlops/` (Cursor)
- `.codex/mlops/` (Codex)
- `.opencode/mlops/` (OpenCode)
- `mlops/` (universal fallback)

## Task-Type Awareness

Metrics and validation adapt to the problem type:
- **classification**: accuracy, precision, recall, f1, auc_roc
- **regression**: rmse, mae, r2
- **mmm**: r2, mape, channel_roi, channel_contribution
- **segmentation**: silhouette_score, n_clusters
- **time_series**: rmse, mae, mape

## Report Bus Integration (v1.2.0)

Reads model, feature, experiment, and data reports from the report bus to cross-reference with registry entries. Writes a registry summary report:
```python
from ml_utils import save_agent_report
save_agent_report("registry-inspector", {
    "status": "completed",
    "findings": {"models": 2, "features": 15, "experiments": 5, "data_versions": 1},
    "recommendations": [],
    "artifacts": []
})
```

## Full Specification

See `commands/registry.md` for complete subcommand routing, table formats, and lineage tracing instructions.
