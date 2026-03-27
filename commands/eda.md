---
name: eda
description: "Perform exploratory data analysis on any dataset. Generates comprehensive statistics, visualizations, and insights about data quality, distributions, correlations, and patterns. Works with CSV, Excel, JSON, or any tabular data."
user_invocable: true
aliases: ["explore", "analyze-data", "data-analysis"]
---

# Exploratory Data Analysis (EDA) Skill

You are performing comprehensive exploratory data analysis on any provided dataset. This works with any tabular data format.

## Your EDA Workflow

### 1. Data Overview
- Load the dataset and display shape, columns, and data types
- Show first and last few rows
- Identify the target variable (if classification/regression)

### 2. Data Quality Assessment
- Check for missing values (count and percentage per column)
- Identify duplicate rows
- Detect potential data type mismatches
- Find columns with constant or near-constant values

### 3. Statistical Summary
- Generate descriptive statistics for numerical columns
- Value counts and frequency distributions for categorical columns
- Identify outliers using IQR method or z-scores

### 4. Distribution Analysis
- Plot histograms for numerical features
- Bar charts for categorical features
- Box plots to visualize outliers

### 5. Correlation Analysis
- Compute correlation matrix for numerical features
- Visualize with heatmap
- Identify highly correlated feature pairs (>0.8 or <-0.8)

### 6. Target Variable Analysis (if applicable)
- Class distribution for classification
- Target distribution for regression
- Feature importance with respect to target

### 7. Key Findings Summary
- Summarize data quality issues
- Highlight potential feature engineering opportunities
- Note any red flags for modeling

### 8. Save Structured EDA Report

**CRITICAL**: Always save a structured EDA report for downstream agents (especially feature engineering):

```python
# Copy ml_utils.py from plugin templates if not present
import shutil, os
# Try multiple plugin installation paths (Claude Code, Cursor, Codex, OpenCode)
from pathlib import Path
_PLUGIN_PATHS = [
    Path.home() / ".claude" / "plugins" / "ml-automation" / "templates" / "ml_utils.py",
    Path.home() / ".cursor" / "plugins" / "ml-automation" / "templates" / "ml_utils.py",
    Path.home() / ".codex" / "plugins" / "ml-automation" / "templates" / "ml_utils.py",
    Path.home() / ".config" / "opencode" / "ml-automation" / "templates" / "ml_utils.py",
]
utils_src = next((str(p) for p in _PLUGIN_PATHS if p.exists()), None)
if utils_src is None:
    print("Warning: ml_utils.py not found in any known plugin path")
if utils_src and os.path.exists(utils_src) and not os.path.exists("src/ml_utils.py"):
    os.makedirs("src", exist_ok=True)
    shutil.copy2(utils_src, "src/ml_utils.py")

from src.ml_utils import generate_eda_summary, save_eda_report

eda_summary = generate_eda_summary(df, target_col=target_col)
save_eda_report(eda_summary)  # Saves to .claude/eda_report.json

# Also save human-readable report
os.makedirs("reports", exist_ok=True)
# ... save markdown report to reports/eda_report.md
```

This structured report is automatically consumed by the `feature-engineering-analyst` agent to make informed feature engineering decisions.

## Reusable Utilities

Before writing boilerplate code, check if `src/ml_utils.py` exists in the project. If not, copy it from the plugin templates:

```python
import shutil, os
# Try multiple plugin installation paths (Claude Code, Cursor, Codex, OpenCode)
from pathlib import Path
_PLUGIN_PATHS = [
    Path.home() / ".claude" / "plugins" / "ml-automation" / "templates" / "ml_utils.py",
    Path.home() / ".cursor" / "plugins" / "ml-automation" / "templates" / "ml_utils.py",
    Path.home() / ".codex" / "plugins" / "ml-automation" / "templates" / "ml_utils.py",
    Path.home() / ".config" / "opencode" / "ml-automation" / "templates" / "ml_utils.py",
]
utils_src = next((str(p) for p in _PLUGIN_PATHS if p.exists()), None)
if utils_src is None:
    print("Warning: ml_utils.py not found in any known plugin path")
if utils_src and not os.path.exists("src/ml_utils.py"):
    os.makedirs("src", exist_ok=True)
    shutil.copy2(utils_src, "src/ml_utils.py")
```

Use these functions instead of reimplementing:
- `load_data(path)` — loads CSV/Excel/JSON/Parquet
- `detect_column_types(df, target_col)` — classifies columns
- `generate_eda_summary(df, target_col)` — creates structured summary
- `save_eda_report(report_data)` — persists report for downstream agents

### Extension Hook Point: after-eda

Scan for extension agents with `hooks_into` containing "after-eda":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "after-eda"
3. Spawn each matching agent with current report context
4. On failure: log warning, continue

## Output Format

Provide findings in clear sections with:
- Code cells for analysis
- Markdown cells explaining insights
- Visualizations where helpful

**IMPORTANT**: After completing EDA, proactively invoke the `ml-theory-advisor` agent to review findings for potential data leakage risks or modeling concerns.
