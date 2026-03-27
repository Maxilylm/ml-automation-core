---
name: evaluate
description: "Comprehensive model evaluation with appropriate metrics, visualizations, and interpretation. Includes confusion matrix, ROC curves, feature importance, and error analysis."
user_invocable: true
---

# Model Evaluation Skill

You are performing comprehensive model evaluation with proper methodology.

## Evaluation Workflow

### 1. Classification Metrics
For classification problems, compute and explain:
```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
```

- **Accuracy**: Overall correctness (use with caution for imbalanced data)
- **Precision**: Of predicted positives, how many are correct
- **Recall**: Of actual positives, how many were found
- **F1-Score**: Harmonic mean of precision and recall
- **ROC-AUC**: Model's ability to discriminate between classes

### 2. Confusion Matrix Analysis
- Visualize confusion matrix with seaborn heatmap
- Analyze false positives vs false negatives
- Discuss business implications of each error type

### 3. ROC and Precision-Recall Curves
```python
from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay
RocCurveDisplay.from_estimator(model, X_test, y_test)
PrecisionRecallDisplay.from_estimator(model, X_test, y_test)
```

### 4. Feature Importance
- For tree-based models: feature_importances_
- For linear models: coefficients
- SHAP values for model-agnostic interpretation

### 5. Error Analysis
- Examine misclassified samples
- Look for patterns in errors
- Identify potential model weaknesses

### 6. Cross-Validation Stability
- Report mean and std of CV scores
- Check for high variance (potential overfitting)
- Compare train vs validation performance

## Metrics Selection Guide

| Problem Type | Primary Metrics | When to Use |
|-------------|-----------------|-------------|
| Balanced Classification | Accuracy, F1 | Equal class importance |
| Imbalanced Classification | F1, ROC-AUC, PR-AUC | Rare positive class |
| Cost-Sensitive | Custom weighted metrics | Different error costs |
| Regression | RMSE, MAE, R² | Continuous targets |

### Extension Hook Point: after-evaluation

Scan for extension agents with `hooks_into` containing "after-evaluation":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "after-evaluation"
3. Spawn each matching agent with current report context
4. On failure: log warning, continue

## Output Format

Provide:
1. **Metrics Summary Table**: All relevant metrics in one place
2. **Visualizations**: Confusion matrix, ROC curve, feature importance
3. **Interpretation**: What the metrics mean for this specific problem
4. **Recommendations**: Next steps based on evaluation results

**IMPORTANT**: After evaluation, invoke the `ml-theory-advisor` agent to validate the evaluation methodology and interpret results in context.
