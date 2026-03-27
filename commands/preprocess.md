---
name: preprocess
description: "Data processing pipeline creation for any tabular data. Handles missing values, encoding, scaling, and transformations. For ML tasks, ensures no data leakage."
user_invocable: true
aliases: ["process", "clean", "transform"]
---

# Data Processing Skill

You are creating a robust data processing pipeline. For ML tasks, this prevents data leakage. For analysis tasks, this ensures clean, consistent data.

## Preprocessing Workflow

### 0. Initialize Reusable Utilities

Before writing boilerplate, copy the shared utilities into the project:

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

from src.ml_utils import detect_column_types, build_preprocessor, safe_split, load_eda_report
```

Also check for prior EDA reports to inform preprocessing decisions:

```python
eda_report = load_eda_report()
if eda_report:
    print(f"Found EDA report: {eda_report['shape']['rows']} rows, {eda_report['shape']['cols']} cols")
    print(f"Quality issues: {len(eda_report.get('quality_issues', []))}")
    # Use this to inform imputation, scaling, and encoding choices
```

### 1. Identify Column Types
```python
# Use the reusable utility instead of manual detection
col_types = detect_column_types(df, target_col=target_col)
numerical_cols = col_types["numerical"]
categorical_cols = col_types["categorical"]
```

### 1b. Feature-Target Leakage Scan

Before building the pipeline, check for leakage signals:

```python
import numpy as np

# Check feature-target correlations
target = df[target_col]
num_features = df.select_dtypes('number').drop(columns=[target_col], errors='ignore')
correlations = num_features.corrwith(target).abs().sort_values(ascending=False)
high_corr = correlations[correlations > 0.90]
if len(high_corr) > 0:
    print("WARNING: Features with >0.90 correlation to target (possible leakage):")
    print(high_corr)

# Check for derived columns (feature-feature near-perfect correlation)
corr_matrix = num_features.corr().abs()
for i in range(len(corr_matrix)):
    for j in range(i+1, len(corr_matrix)):
        if corr_matrix.iloc[i, j] > 0.95:
            print(f"WARNING: {corr_matrix.columns[i]} vs {corr_matrix.columns[j]}: {corr_matrix.iloc[i,j]:.3f} — possible derived column")

# Drop confirmed leaky features
# leaky_cols = [...]
# df = df.drop(columns=leaky_cols)
```

### 2. Missing Value Strategy
- **Numerical**: Median imputation (robust to outliers) or mean
- **Categorical**: Mode imputation or 'Unknown' category
- **Advanced**: KNN imputation, iterative imputation

```python
from sklearn.impute import SimpleImputer, KNNImputer

num_imputer = SimpleImputer(strategy='median')
cat_imputer = SimpleImputer(strategy='most_frequent')
```

### 3. Encoding Categorical Variables
- **Nominal (no order)**: OneHotEncoder
- **Ordinal (has order)**: OrdinalEncoder with specified order
- **High cardinality**: TargetEncoder (careful of leakage!)

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

# For nominal categories
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

# For ordinal categories
ordinal_encoder = OrdinalEncoder(categories=[['low', 'medium', 'high']])
```

### 4. Scaling Numerical Features
- **StandardScaler**: When features should have zero mean, unit variance
- **MinMaxScaler**: When bounded range [0,1] is needed
- **RobustScaler**: When data has outliers

```python
from sklearn.preprocessing import StandardScaler, RobustScaler

scaler = StandardScaler()  # Most common choice
```

### 5. Build Complete Pipeline
```python
# Quick version using reusable utility:
preprocessor = build_preprocessor(numerical_cols, categorical_cols)

# Or customize if EDA revealed specific needs:
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

num_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

cat_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer([
    ('num', num_pipeline, numerical_cols),
    ('cat', cat_pipeline, categorical_cols)
])
```

### 6. Feature Engineering (Optional)
- Polynomial features for non-linear relationships
- Binning for continuous variables
- Interaction features
- Domain-specific transformations

### 7. Save Pipeline Artifact

```python
import joblib, os
os.makedirs("models", exist_ok=True)
joblib.dump(preprocessor, "models/preprocessing_pipeline.joblib")
print(f"Pipeline saved to models/preprocessing_pipeline.joblib")
```

## Data Leakage Prevention Checklist

- [ ] Run leakage scan (step 1b) — no feature-target correlation >0.90
- [ ] No derived columns (feature-feature correlation >0.95)
- [ ] Split data BEFORE preprocessing
- [ ] Fit transformers on training data ONLY
- [ ] Transform (not fit_transform) on test data
- [ ] No target information in features
- [ ] No future information in features (time series)

### Extension Hook Point: after-preprocessing

Scan for extension agents with `hooks_into` containing "after-preprocessing":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "after-preprocessing"
3. Spawn each matching agent with current report context
4. On failure: log warning, continue

## Output

Provide:
1. Column type identification
2. Leakage scan results (any flagged/dropped features)
3. Missing value analysis and strategy
4. Complete preprocessing pipeline code
5. Saved pipeline artifact path
6. Instructions for fitting and transforming

**IMPORTANT**: After creating the preprocessing pipeline, invoke the `ml-theory-advisor` agent to verify no data leakage risks exist in the pipeline design.
