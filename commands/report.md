---
name: report
description: "Generate ad-hoc reports and dashboards for any data project. Supports EDA reports, performance reports, drift monitoring, and project status summaries."
user_invocable: true
aliases: ["generate-report", "summary"]
---

# Report Skill - Generate Reports and Dashboards

You are generating reports for various aspects of any data project.

## Overview

The `/report` command generates:
- **eda** - Exploratory data analysis report
- **model** - Model performance report
- **drift** - Data drift monitoring report
- **project** - Project status report
- **metrics** - Model metrics dashboard

## Usage

```bash
# Generate EDA report
/report eda data/raw/titanic.csv

# Generate model performance report
/report model

# Generate drift report
/report drift --baseline data/processed/baseline.csv --current data/processed/current.csv

# Generate project status report
/report project

# Generate metrics dashboard
/report metrics --output reports/metrics.html
```

## Report Types

### EDA Report

**Command:** `/report eda [data_path]`

**Generates:**
- Data overview and summary statistics
- Missing value analysis
- Distribution visualizations
- Correlation analysis
- Target variable analysis
- Feature recommendations

**Output Format:**
```markdown
# Exploratory Data Analysis Report

## Dataset Overview
- **File**: titanic.csv
- **Rows**: 891
- **Columns**: 12
- **Memory**: 84 KB

## Data Quality Summary
| Metric | Value |
|--------|-------|
| Missing Values | 866 (8.1%) |
| Duplicate Rows | 0 |
| Constant Columns | 0 |

## Column Analysis
| Column | Type | Unique | Missing % | Notes |
|--------|------|--------|-----------|-------|
| Survived | int | 2 | 0% | Target (38% positive) |
| Pclass | int | 3 | 0% | Strong predictor |
| Sex | str | 2 | 0% | Strong predictor |
| Age | float | 88 | 19.9% | Needs imputation |
| ... | ... | ... | ... | ... |

## Key Findings
1. **Class imbalance**: 38% survival rate
2. **Missing values**: Age (19.9%), Cabin (77.1%), Embarked (0.2%)
3. **Strong predictors**: Sex, Pclass, Fare

## Recommendations
1. Drop Cabin column (too many missing values)
2. Impute Age using median by Pclass
3. Create FamilySize feature from SibSp + Parch
4. Extract Title from Name column
```

### Model Performance Report

**Command:** `/report model`

**Generates:**
- Current model metrics
- Confusion matrix
- ROC curve analysis
- Feature importance
- Model comparison (if multiple)

**Output Format:**
```markdown
# Model Performance Report

## Model Summary
- **Type**: RandomForestClassifier
- **Version**: v1.0
- **Trained**: 2024-01-15

## Evaluation Metrics
| Metric | Train | Test | CV (5-fold) |
|--------|-------|------|-------------|
| Accuracy | 0.92 | 0.85 | 0.84 ± 0.03 |
| Precision | 0.90 | 0.83 | 0.82 ± 0.04 |
| Recall | 0.88 | 0.79 | 0.78 ± 0.05 |
| F1 Score | 0.89 | 0.81 | 0.80 ± 0.04 |
| AUC-ROC | 0.95 | 0.88 | 0.87 ± 0.03 |

## Confusion Matrix
|  | Predicted 0 | Predicted 1 |
|--|-------------|-------------|
| Actual 0 | 95 (TN) | 14 (FP) |
| Actual 1 | 15 (FN) | 55 (TP) |

## Feature Importance
| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Sex_encoded | 0.32 |
| 2 | Pclass | 0.21 |
| 3 | Fare | 0.18 |
| 4 | Age | 0.15 |
| 5 | FamilySize | 0.08 |

## Model Comparison
| Model | Accuracy | F1 | AUC |
|-------|----------|-----|-----|
| Logistic Regression | 0.79 | 0.74 | 0.82 |
| Random Forest | 0.85 | 0.81 | 0.88 |
| XGBoost | 0.84 | 0.80 | 0.87 |

## Recommendations
1. Random Forest selected as best model
2. Consider feature engineering for Age
3. Monitor for overfitting (train-test gap)
```

### Drift Report

**Command:** `/report drift`

**Generates:**
- Feature distribution comparisons
- Statistical drift tests
- Drift alerts
- Recommended actions

**Output Format:**
```markdown
# Data Drift Report

## Summary
- **Baseline Period**: 2024-01-01 to 2024-01-15
- **Current Period**: 2024-01-16 to 2024-01-31
- **Overall Drift**: ⚠️ DETECTED

## Feature Drift Analysis
| Feature | Test | Statistic | p-value | Status |
|---------|------|-----------|---------|--------|
| Age | KS | 0.12 | 0.23 | ✅ OK |
| Fare | KS | 0.25 | 0.01 | ⚠️ DRIFT |
| Pclass | Chi² | 8.5 | 0.04 | ⚠️ DRIFT |
| Sex | Chi² | 0.3 | 0.85 | ✅ OK |

## Drift Details

### Fare (DRIFT DETECTED)
- Baseline mean: $32.20
- Current mean: $45.80
- Change: +42.2%
- Likely cause: Higher class passengers in recent data

### Pclass (DRIFT DETECTED)
- Baseline distribution: [24%, 21%, 55%]
- Current distribution: [35%, 25%, 40%]
- Change: More first-class passengers

## Recommendations
1. Investigate source of Fare drift
2. Consider retraining model with recent data
3. Monitor prediction distribution for concept drift
```

### Project Status Report

**Command:** `/report project`

**Generates:**
- Task completion status
- PR status
- Test coverage
- Deployment status
- Timeline

**Output Format:**
```markdown
# Project Status Report

## Overview
- **Project**: Titanic Survival Prediction
- **Status**: ✅ Production Ready
- **Last Updated**: 2024-01-15

## Pipeline Status
| Stage | Status | Details |
|-------|--------|---------|
| Data Ingestion | ✅ Complete | 891 rows loaded |
| EDA | ✅ Complete | Report generated |
| Preprocessing | ✅ Complete | Pipeline created |
| Model Training | ✅ Complete | RF selected (85% acc) |
| Evaluation | ✅ Complete | Validated |
| Deployment | ✅ Complete | Docker + Snowflake |

## Code Quality
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Test Coverage | 87% | 80% | ✅ |
| Lint Errors | 0 | 0 | ✅ |
| Type Errors | 3 | 10 | ✅ |
| Security Issues | 0 | 0 | ✅ |

## PR Summary
| PR | Title | Status | Reviewers |
|----|-------|--------|-----------|
| #1 | Add preprocessing | ✅ Merged | code-reviewer |
| #2 | Add model training | ✅ Merged | ml-advisor |
| #3 | Add API | ✅ Merged | mlops |

## Artifacts
- Model: models/model_v1.joblib
- API: http://localhost:8000
- Dashboard: Snowflake TITANIC_DASHBOARD

## Next Steps
1. Set up production monitoring
2. Configure alerting
3. Plan retraining schedule
```

### Metrics Dashboard

**Command:** `/report metrics`

**Generates:**
- Real-time metrics visualization
- Performance trends
- Prediction distribution
- Latency charts
- EDA deep dive (distributions, correlations, missing values, outlier detection)
- Live inference panel (if model artifacts exist in models/ directory)
- What-if analysis (feature sensitivity for trained models)

**Output:**
Interactive HTML dashboard saved to reports/metrics.html

**Interactive Features:**
- If model artifacts are found (`models/*.joblib`, `models/*.pkl`):
  - Input form with widgets matching each feature's type
  - Real-time prediction with confidence/probability display
  - Feature sensitivity sliders for what-if analysis
- EDA section always included with full distribution and correlation analysis
- Data explorer with filtering, sorting, and CSV download

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output file path | reports/{type}_{timestamp}.md |
| `--format` | Output format (md, html, pdf, json) | md |
| `--verbose` | Include detailed analysis | false |
| `--save-plots` | Save visualizations | true |

## Agent Coordination

This skill may invoke:
- **eda-analyst** - For EDA report generation
- **ml-theory-advisor** - For model analysis
- **eda-analyst** - For drift analysis
- **mlops-engineer** - For project status

## Output Location

Reports are saved to:
```
reports/
├── eda_report_20240115.md
├── model_report_20240115.md
├── drift_report_20240115.md
├── project_report_20240115.md
├── metrics_dashboard.html
└── figures/
    ├── correlation_matrix.png
    ├── feature_importance.png
    └── roc_curve.png
```
