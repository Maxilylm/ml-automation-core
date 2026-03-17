---
name: eda
description: Perform exploratory data analysis on any dataset. Generates comprehensive statistics, visualizations, and insights about data quality, distributions, correlations, and patterns. Works with CSV, Excel, JSON, or any tabular data.
---

# Exploratory Data Analysis (EDA)

## When to Use
- Exploring a new dataset
- Investigating data quality issues
- Understanding variable relationships and patterns
- Preparing data summaries for stakeholders

## Workflow

1. **Data Overview** - Load dataset, display shape, columns, data types, first/last rows
2. **Data Quality Assessment** - Missing values, duplicates, type mismatches, constant columns
3. **Statistical Summary** - Descriptive stats for numerical, value counts for categorical, outlier detection
4. **Distribution Analysis** - Histograms, bar charts, box plots
5. **Correlation Analysis** - Correlation matrix, heatmap, highly correlated pairs (>0.8 or <-0.8)
6. **Target Variable Analysis** - Class distribution, feature importance vs target
7. **Key Findings Summary** - Data quality issues, feature engineering opportunities, modeling red flags

## Output Format

Provide findings in clear sections with code cells, markdown explanations, and visualizations.

After completing EDA, invoke the `ml-theory-advisor` agent to review findings for potential data leakage risks.

## Report Bus Integration (v1.2.0)

Write a structured EDA report for downstream agents:
```python
from ml_utils import save_agent_report
save_agent_report("eda-analyst", {
    "status": "completed",
    "findings": {"rows": 500, "columns": 12, "quality_issues": 3, "key_patterns": [...]},
    "recommendations": [{"text": "Impute Age column", "target_agent": "preprocessor"}],
    "artifacts": [".claude/eda_report.json", "reports/figures/"]
})
```

## Data Versioning (v1.3.0)

Generate a data fingerprint and register in the data versions registry for reproducibility. Use `ml_utils.compute_data_fingerprint()` if available.

## Full Specification

See `commands/eda.md` for complete EDA workflow, visualization patterns, and ml_utils integration.
