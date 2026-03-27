---
name: train
description: "Train a machine learning model with proper data splitting, preprocessing, and validation. Follows best practices to avoid data leakage and overfitting."
user_invocable: true
---

# Model Training Skill

You are training a machine learning model following rigorous best practices.

## Training Workflow

### 0. Initialize Reusable Utilities

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

from src.ml_utils import (
    load_data, detect_column_types, build_preprocessor,
    safe_split, evaluate_model, load_eda_report
)
```

### Extension Hook Point: before-training

Scan for extension agents with `hooks_into` containing "before-training":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "before-training"
3. Spawn each matching agent with current report context
4. On failure: log warning, continue

### 1. Data Preparation
- Load and validate the dataset
- Separate features (X) from target (y)
- **CRITICAL**: Split data BEFORE any preprocessing
  ```python
  # Use the leakage-safe split utility:
  X_train, X_test, y_train, y_test = safe_split(df, target_col=target_col)
  ```

### 2. Preprocessing Pipeline
- Create preprocessing steps using sklearn Pipeline
- Fit transformers ONLY on training data
- Apply to both train and test sets
```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

preprocessor = ColumnTransformer(transformers=[
    ('num', StandardScaler(), numerical_cols),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
])
```

### 3. Model Selection
- Start with a simple baseline (e.g., LogisticRegression, DecisionTree)
- Use cross-validation on training set only
```python
from sklearn.model_selection import cross_val_score
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
```

### 4. Hyperparameter Tuning
- Use GridSearchCV or RandomizedSearchCV
- Tune on training/validation data only
- Never use test set for tuning decisions

### 5. Final Evaluation
- Train final model on full training set
- Evaluate ONCE on held-out test set
- Report appropriate metrics for the problem type

## Best Practices Enforced

- NO fitting on full data before splitting
- NO target leakage in features
- NO evaluation metrics on training data as final results
- ALWAYS use pipelines to prevent data leakage
- ALWAYS set random_state for reproducibility

### Extension Hook Point: after-training

Scan for extension agents with `hooks_into` containing "after-training":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "after-training"
3. Spawn each matching agent with current report context
4. On failure: log warning, continue

## Output

Provide:
- Training code with clear documentation
- Cross-validation results
- Final test set performance
- Model summary and next steps

**IMPORTANT**: After training, invoke the `ml-theory-advisor` agent to review the pipeline for potential issues, and the `brutal-code-reviewer` agent to ensure code quality.
