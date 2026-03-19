---
name: team-coldstart
description: "Launch a full data workflow from raw data to deployed solution with interactive dashboard. Orchestrates multiple agents through analysis, processing, modeling, and deployment stages. Works with any tabular data."
user_invocable: true
aliases: ["team coldstart", "coldstart", "full-pipeline", "run-all"]
---

# Team Cold Start - Full Data Workflow Orchestration

You are launching a complete data workflow from raw data to deployed solution with an interactive Streamlit dashboard. This skill orchestrates multiple specialized agents through all stages of the data lifecycle.

## Overview

The `/team coldstart` command initiates an end-to-end data pipeline:
1. **Initialize** - Set up project, validate data, detect data type
2. **Analyze** - EDA, quality review, feature/column recommendations
3. **Process** - Build and validate data processing pipeline
4. **Model** - Train and compare models (if prediction task) OR generate insights (if analysis task)
5. **Evaluate** - Comprehensive evaluation with metrics and visualizations
6. **Dashboard** - Create interactive Streamlit dashboard with results
7. **Productionalize** - Create production-ready code and API
8. **Deploy** - Deploy to target environment (optional)
9. **Finalize** - Generate reports, merge PRs

## Usage

```bash
# Full pipeline with auto-detection
/team coldstart data/raw/sales.csv

# With specific target variable (ML task)
/team coldstart data/raw/customers.csv --target Churn

# Analysis-only mode (no ML, just insights + dashboard)
/team coldstart data/raw/survey.csv --mode analysis

# Skip deployment stage
/team coldstart data/raw/data.csv --no-deploy

# Deploy to specific target
/team coldstart data/raw/data.csv --deploy-to snowflake

# Custom dashboard title
/team coldstart data/raw/data.csv --dashboard-title "Sales Analytics"
```

## Stage Flow Pattern (v1.4.0)

Every stage from 2 onwards follows this enhanced flow:

```
1. LOAD LESSONS — get_relevant_lessons(stage) from lessons-learned.json
2. PRE-STAGE REFLECTION — domain expert reads reports + lessons, produces stage plan
3. EXECUTE — agent runs the stage, reading the stage plan first
4. SELF-CHECK — validate_stage_output() runs deterministic checks
   └── If fails: re-spawn agent with error feedback (max --max-check iterations)
   └── On persistent failure: save_lesson() recording the issue
5. POST-STAGE REFLECTION GATE — (existing v1.2.1) ml-theory-advisor validates strategy
   └── If revise: save_lesson() recording the correction
6. PROCEED to next stage
```

### Pre-Stage Reflection Prompt Template

Before each stage, spawn the appropriate reflector agent (unless `--no-pre-reflect`):

```
PRE-STAGE REFLECTION — Stage {N}: {stage_name}

Read ALL reports in .claude/reports/ for context on prior stages.
Read .claude/lessons-learned.json for relevant lessons from past runs.

Produce a stage plan with:
1. OBJECTIVES: What this stage must accomplish
2. APPROACH: Recommended strategy based on prior findings
3. RISKS: Potential issues to watch for (from lessons + reports)
4. SUCCESS CRITERIA: How to verify the stage succeeded

Save your plan using save_stage_plan("{stage_name}", {...})
```

| Stage | Reflector Agent |
|-------|----------------|
| 2 (Analysis) | ml-theory-advisor |
| 3 (Processing) | ml-theory-advisor |
| 4 (Modeling) | ml-theory-advisor |
| 5 (Evaluation) | ml-theory-advisor |
| 6 (Dashboard) | frontend-ux-analyst |
| 7 (Production) | mlops-engineer |

### Self-Check Loop Template

After each stage's agent completes (unless `--max-check 0`):

```
iteration = 0
max_iterations = {--max-check, default: 2}

Run validate_stage_output("{stage_name}")
while validation fails AND iteration < max_iterations:
    Re-spawn agent with:
      "SELF-CHECK FAILED (attempt {iteration+1}/{max_iterations}):
       {error_list}
       FIRST: Read the stage plan at .claude/reports/stage_plan_{stage_name}.json
       Fix the issues identified above and complete the stage."
    Run validate_stage_output() again
    iteration += 1

If still failing after max_iterations:
    save_lesson({
        "stage": "{stage_name}",
        "category": "mistake",
        "severity": "high",
        "title": "Stage {stage_name} failed validation after {max_iterations} retries",
        "description": "Errors: {error_list}",
        "trigger": "validate_stage_output() failure",
        "tags": ["{stage_name}", "validation-failure"]
    })
    Log warning and proceed with best effort
```

### Lessons Integration

Before each stage, load and format relevant lessons (unless `--no-lessons`):
```python
from ml_utils import get_relevant_lessons, format_lessons_for_prompt

lessons = get_relevant_lessons(stage="{stage_name}")
lessons_text = format_lessons_for_prompt(lessons)
# Append lessons_text to the agent's spawn prompt
```

When a post-stage reflection gate requests revision:
```python
from ml_utils import save_lesson

save_lesson({
    "stage": "{stage_name}",
    "category": "mistake",
    "severity": "medium",
    "title": "Reflection gate correction: {brief description}",
    "description": "{full correction details from reflection report}",
    "resolution": "{what the revised approach should be}",
    "tags": ["{stage_name}", "reflection-gate"],
    "applicable_to": ["team-coldstart"]
})
```

## Your Orchestration Workflow

### Stage 1: Initialize

**Actions:**
1. Create feature branch: `feature/data-pipeline-{timestamp}`
2. Create task list for tracking progress
3. Validate input data exists and is readable
4. Auto-detect data type and task mode:
   - **ML Mode**: Target column specified or detectable (classification/regression)
   - **Analysis Mode**: No clear target, focus on insights and visualization
5. Set up project structure

**Tasks to Create:**
- [ ] Initialize project structure
- [ ] Validate input data quality
- [ ] Run exploratory data analysis
- [ ] Build data processing pipeline
- [ ] Train models OR generate insights
- [ ] Evaluate results
- [ ] Create Streamlit dashboard
- [ ] Create production code
- [ ] Deploy (if requested)
- [ ] Generate final report

**Output:**
```markdown
## Stage 1: Initialize ✓

- Branch: feature/data-pipeline-20240115-1030
- Data validated: data/raw/sales.csv (10000 rows, 25 columns)
- Detected mode: ML (target: Revenue) OR Analysis (no target)
- Quality check: PASSED (no critical issues)
```

### Stage 2: Analysis (Sequential → Parallel with Report Bus)

#### Stage 2 Pre-Reflection (unless --no-pre-reflect)

Spawn **ml-theory-advisor** in pre-reflection mode:

```
PRE-STAGE REFLECTION — Stage 2: Analysis

Read any prior reports in .claude/reports/ and .claude/lessons-learned.json.
This is the first analysis stage. Plan what EDA should focus on based on:
- The data file characteristics (columns, size)
- Any lessons from prior workflow runs
- Known data quality patterns to check

Save your plan using save_stage_plan("analysis", {...})
```

After the plan is saved, proceed to Step 2a. Include in the eda-analyst prompt:
"FIRST: Read the stage plan at .claude/reports/stage_plan_analysis.json. Follow its objectives and watch for identified risks."

**Step 2a: Run EDA first** (generates report for downstream agents):

1. **eda-analyst** - Comprehensive EDA + Report Bus Output
   ```
   Perform thorough exploratory data analysis on {data_path}.
   Generate statistics, visualizations, and identify data quality issues.

   CRITICAL: Use ml_utils to save structured EDA report:
   - Copy ml_utils.py from the plugin templates if not present in src/
   - Call generate_eda_summary(df, target_col) and save_eda_report(summary)
   - Also save reports/eda_report.md with narrative findings
   - The save_eda_report function will automatically write to the report bus

   Output: EDA report + agent bus report (eda-analyst_report.json)
   ```

   After EDA completes, the data fingerprint is automatically generated by eda-analyst
   and stored in `.claude/mlops/data-versions/`. This enables downstream reproducibility.

#### Step 2a-check: EDA Self-Check

Run `validate_stage_output("eda")`. If validation fails, re-spawn eda-analyst with error feedback (max `--max-check` iterations). On persistent failure, `save_lesson()` documenting the issue.

**Step 2b: Run these in PARALLEL** (after EDA completes — they all read the EDA report independently):

Spawn ALL THREE agents concurrently using multiple Task tool calls in a single message:

2. **ml-theory-advisor** - Data quality and leakage review (if ML mode)
   ```
   Review the dataset {data_path} for potential data leakage risks.
   Check for features that may contain target information.
   FIRST: Read .claude/reports/eda-analyst_report.json (or .claude/eda_report.json) for prior EDA context.
   Validate data splitting strategy.
   WHEN DONE: Write your report using save_agent_report("ml-theory-advisor", {...})
   Output: Quality and leakage assessment report + agent bus report
   ```

3. **feature-engineering-analyst** - ML Feature Engineering
   ```
   Analyze {data_path} and engineer predictive features.
   FIRST: Read .claude/reports/eda-analyst_report.json (or .claude/eda_report.json) — use the EDA findings
   to inform your feature engineering strategy.
   WHEN DONE: Write your report using save_agent_report("feature-engineering-analyst", {...})
   Output: Feature engineering plan + agent bus report
   ```

   After feature engineering completes, all features are registered in `.claude/mlops/feature-store.json`
   by feature-engineering-analyst. This enables feature reuse and lineage tracking.

4. **frontend-ux-analyst** - Dashboard Planning
   ```
   Review the EDA findings for {data_path} to plan an interactive dashboard with live inference.
   FIRST: Read .claude/reports/eda-analyst_report.json for data context.
   ALSO: Check if model artifacts exist in models/ directory (joblib/pickle files).
   Plan dashboard with these priorities:
   1. Rich EDA exploration: distributions, correlations, missing value patterns, outlier detection
   2. If a model exists: live inference tab where users input feature values and get real-time predictions
   3. What-if analysis: sliders/inputs to tweak features and see prediction changes
   4. Segment comparison: filter by categorical groups and compare distributions/outcomes
   Recommend dashboard layout, key visualizations, widget types, and interaction flows.
   WHEN DONE: Write your report using save_agent_report("frontend-ux-analyst", {...})
   Output: Dashboard design recommendations + agent bus report
   ```

**Wait for all three to complete, then run Step 2b-verify.**

#### Step 2b-verify: Report Bus Verification

After all three parallel agents return, check that each wrote its report:

```
For each agent in [ml-theory-advisor, feature-engineering-analyst, frontend-ux-analyst]:
  1. Check if .claude/reports/{agent}_report.json exists
  2. If MISSING — re-spawn that agent ONCE with this prefix:
     "REPORT MISSING — your prior run did not save a report.
      You MUST call save_agent_report('{agent}', {{...}}) before finishing.
      Re-read .claude/reports/eda-analyst_report.json and complete your analysis."
  3. After the retry, check again. If still missing, log a warning:
     "WARNING: {agent} report missing after retry — proceeding without it."
```

Only proceed to Stage 2c after verification completes.

#### Step 2b-check: Feature Engineering Self-Check

Run `validate_stage_output("feature-engineering")`. If validation fails, re-spawn feature-engineering-analyst with error feedback (max `--max-check` iterations).

**Output:**
```markdown
## Stage 2: Analysis ✓

### EDA Summary
- Dataset: {rows} rows x {cols} columns
- Target: {target} ({type}) OR None (analysis mode)
- Key columns: {list}
- Missing values: {count} columns with >5% missing
- Recommendations: {list}

### Parallel Analysis Results
- Feature Engineering: {count} features recommended
- ML Theory: {leakage_status}, {methodology_notes}
- Dashboard Planning: {visualization_recommendations}
```

### Stage 2c: Gate 1 — Reflect on Feature Engineering (Reflection Loop)

**Reflection gate** — validates feature engineering output before preprocessing proceeds.

```
iteration = 0
max_iterations = {--max-reflect, default: 2}
```

1. **Spawn ml-theory-advisor in reflection mode:**
   ```
   REFLECTION MODE — Gate 1: Post-Feature-Engineering

   Read ALL reports in .claude/reports/, especially:
   - eda-analyst_report.json
   - feature-engineering-analyst_report.json

   Evaluate whether the proposed feature engineering strategy is sound:
   - Are features appropriate for the problem domain?
   - Are domain-specific transformations included (e.g., adstock for MMM, lag for time series)?
   - Any leakage risk in the proposed features?
   - Is variable selection justified?

   Write reflection report using save_reflection_report("post-feature-engineering", {...})
   Your verdict must be either "approved" or "revise" with specific corrections.
   ```

2. **Read reflection report verdict:**
   - If `"verdict": "approved"` → proceed to Stage 3
   - If `"verdict": "revise"` → re-spawn feature-engineering-analyst with corrections:
     ```
     REVISION REQUEST from ml-theory-advisor reflection gate.

     Read the reflection report at .claude/reports/ml-theory-advisor_reflection_post-feature-engineering_report.json
     Address the corrections listed. Update your feature engineering plan accordingly.
     Write your updated report using save_agent_report("feature-engineering-analyst", {...})
     ```
   - Increment iteration, loop back to step 1

3. **If max iterations reached with verdict still "revise":**
   - Log warning: "Gate 1: Max reflection iterations reached, proceeding with best effort"
   - Proceed to Stage 3

### Stage 3: Data Processing

#### Stage 3 Pre-Reflection (unless --no-pre-reflect)

Spawn **ml-theory-advisor** in pre-reflection mode for preprocessing. Reads all prior reports + lessons. Saves plan to `stage_plan_preprocessing.json`.

**Actions:**
1. Build data processing pipeline based on EDA findings
2. Handle missing values, encoding, scaling as needed
3. Invoke `ml-theory-advisor` to validate no leakage (if ML mode)
4. Generate unit tests for processing functions
5. Create PR for processing code
6. Invoke `brutal-code-reviewer` for code review
7. Merge PR after approval

**Code to generate:**
```python
# First, ensure ml_utils.py is in the project (copy from plugin templates if not present)
# src/ml_utils.py provides: load_data, detect_column_types, build_preprocessor, safe_split, etc.

# src/processing.py
from src.ml_utils import detect_column_types, build_preprocessor, load_eda_report

def process_data(df, target_col=None, mode='ml'):
    """Process raw data for modeling or analysis.

    Uses prior EDA report if available to inform preprocessing decisions.
    """
    # Load EDA context if available
    eda_report = load_eda_report()

    # Detect column types (or use EDA report's classification)
    if eda_report and "column_types" in eda_report:
        col_types = eda_report["column_types"]
    else:
        col_types = detect_column_types(df, target_col=target_col)

    # Build preprocessor
    preprocessor = build_preprocessor(col_types["numerical"], col_types["categorical"])

    return preprocessor, col_types
```

**Output:**
```markdown
## Stage 3: Data Processing ✓

- Pipeline created: src/processing.py
- Tests generated: tests/unit/test_processing.py
- Coverage: 92%
- PR #1: Merged ✓
- Quality check: PASSED
```

#### Stage 3-check: Preprocessing Self-Check

Run `validate_stage_output("preprocessing")`. If validation fails, re-spawn developer with error feedback (max `--max-check` iterations).

### Stage 3b: Gate 2 — Reflect on Preprocessing Pipeline (Reflection Loop)

**Reflection gate** — validates preprocessing pipeline before training proceeds.

Same iteration loop pattern as Gate 1, but:
- Gate name: `"post-preprocessing"`
- Reflection prompt focuses on: pipeline design, scaling/encoding choices, data flow correctness, consistency with chosen model family
- Reports to read: preprocessing report + feature-engineering report + EDA report
- On revise: re-run Stage 3 (preprocessing) with corrections from reflection report

### Stage 4: Modeling / Insights Generation

#### Stage 4 Pre-Reflection (unless --no-pre-reflect)

Spawn **ml-theory-advisor** in pre-reflection mode for training. Reads all prior reports + lessons. Saves plan to `stage_plan_training.json`.

**For ML Mode:**
1. Train baseline model (appropriate for task type)
2. Train advanced models (ensemble methods)
3. Invoke `ml-theory-advisor` to review methodology
4. Compare and select best model

**For Analysis Mode:**
1. Generate statistical summaries
2. Create aggregations and pivots
3. Identify key insights and patterns
4. Generate insight report

**Code to generate:**
```python
# src/model.py (ML mode)
def train_model(X, y, model_type='auto'):
    """Train and return best model for the task."""
    ...

# src/insights.py (Analysis mode)
def generate_insights(df, dimensions, metrics):
    """Generate key insights from data."""
    ...
```

**Output (ML Mode):**
```markdown
## Stage 4: Modeling ✓

### Models Trained
| Model | Metric 1 | Metric 2 | Metric 3 |
|-------|----------|----------|----------|
| Baseline | 0.79 | 0.76 | 0.74 |
| Advanced 1 | 0.84 | 0.82 | 0.80 |
| Advanced 2 | 0.85 | 0.83 | 0.81 |

Best model: Advanced 2
PR #2: Merged ✓
```

   After training completes, the developer agent logs the experiment to `.claude/mlops/experiments/`
   including rationale from prior agent reports, hyperparameters, and metrics across all splits.

**Output (Analysis Mode):**
```markdown
## Stage 4: Insights ✓

### Key Findings
1. Revenue increased 23% YoY
2. Top 3 categories drive 65% of sales
3. Regional variance identified

Insights saved: reports/insights.md
PR #2: Merged ✓
```

#### Stage 4-check: Training Self-Check

Run `validate_stage_output("training")`. If validation fails, re-spawn developer with error feedback (max `--max-check` iterations).

### Stage 4b: Gate 3 — Reflect on Training Approach (Reflection Loop)

**Reflection gate** — validates training approach before evaluation proceeds.

Same iteration loop pattern as Gate 1, but:
- Gate name: `"post-training"`
- Reflection prompt focuses on: model family appropriateness for the domain, hyperparameter strategy, validation approach, whether better alternatives exist
- Reports to read: ALL prior reports + training report
- On revise: re-run Stage 4 (training) with corrections from reflection report
- Example: For MMM, might recommend Bayesian regression over gradient boosting

### Stage 5: Evaluation

#### Stage 5 Pre-Reflection (unless --no-pre-reflect)

Spawn **ml-theory-advisor** in pre-reflection mode for evaluation. Reads all prior reports + lessons. Saves plan to `stage_plan_evaluation.json`.

**For ML Mode:**
1. Run comprehensive model evaluation
2. Generate visualizations (confusion matrix, ROC, feature importance)
3. Invoke `ml-theory-advisor` to validate evaluation
4. Generate evaluation report

**For Analysis Mode:**
1. Validate insight accuracy
2. Generate supporting visualizations
3. Cross-check findings with data
4. Generate analysis report

**Output:**
```markdown
## Stage 5: Evaluation ✓

### Performance Summary (ML) / Validation Summary (Analysis)
- Key metrics validated
- Visualizations generated
- Cross-validation complete (ML)
- Insights verified (Analysis)

Methodology validated ✓
```

#### Stage 5-check: Evaluation Self-Check

Run `validate_stage_output("evaluation")`. If validation fails, re-spawn the evaluation agent with error feedback (max `--max-check` iterations).

### Stage 5b: Post-Training Review (PARALLEL)

Spawn ALL THREE review agents concurrently:

1. **brutal-code-reviewer** - Code quality review
   ```
   Review all code written in this workflow for quality and maintainability.
   FIRST: Read all reports in .claude/reports/ for context on what was built.
   WHEN DONE: Write your report using save_agent_report("brutal-code-reviewer", {...})
   Output: Code review report + agent bus report
   ```

2. **ml-theory-advisor** - Methodology validation
   ```
   Review the trained model and evaluation results for methodology issues.
   FIRST: Read all reports in .claude/reports/ for full workflow context.
   WHEN DONE: Write your report using save_agent_report("ml-theory-advisor", {...})
   Output: Theory review report + agent bus report
   ```

3. **frontend-ux-analyst** - Dashboard UX review (if dashboard exists)
   ```
   Review the generated Streamlit dashboard for UX quality.
   FIRST: Read all reports in .claude/reports/ for context.
   WHEN DONE: Write your report using save_agent_report("frontend-ux-analyst", {...})
   Output: UX review report + agent bus report
   ```

**Wait for all three to complete, then run Step 5b-verify.**

#### Step 5b-verify: Report Bus Verification

After all three review agents return, check that each wrote its report:

```
For each agent in [brutal-code-reviewer, ml-theory-advisor, frontend-ux-analyst]:
  1. Check if .claude/reports/{agent}_report.json exists
  2. If MISSING — re-spawn that agent ONCE with this prefix:
     "REPORT MISSING — your prior run did not save a report.
      You MUST call save_agent_report('{agent}', {{...}}) before finishing.
      Re-read all reports in .claude/reports/ and complete your review."
  3. After the retry, check again. If still missing, log a warning:
     "WARNING: {agent} report missing after retry — proceeding without it."
```

Only proceed to Stage 5c after verification completes.

### Stage 5c: MLOps Registry Validation

**mlops-engineer** validates that all MLOps registries are complete:

1. **Spawn mlops-engineer for registry validation:**
   ```
   MLOps Registry Validation — verify all registries are complete.

   Read all reports in .claude/reports/ for context.
   Read all registries in .claude/mlops/ (model-registry.json, feature-store.json, experiments/, data-versions/).

   Validate:
   1. Model registered with correct task_type and metrics
   2. All features cataloged with transformations and lineage
   3. Experiment logged with rationale from prior agent reports
   4. Data fingerprint exists
   5. Lineage chain is complete: data -> features -> experiment -> model

   If any registry is incomplete, fill gaps from available reports.
   Compare new model metrics with champion (if exists) and promote if better.

   Write your report using save_agent_report("mlops-engineer", {...})
   ```

2. **Output:**
   ```markdown
   ## Stage 5c: MLOps Registry Validation ✓

   - Model registered: model_20260223_143022 (challenger -> champion)
   - Features cataloged: 12 features in feature-store.json
   - Experiment logged: exp_20260223_143022
   - Data fingerprinted: sha256:abc123...
   - Lineage: complete ✓
   ```

#### Step 5c-verify: Report Bus Verification

After mlops-engineer returns, check that it wrote its report:

```
1. Check if .claude/reports/mlops-engineer_report.json exists
2. If MISSING — re-spawn mlops-engineer ONCE with this prefix:
   "REPORT MISSING — your prior run did not save a report.
    You MUST call save_agent_report('mlops-engineer', {{...}}) before finishing.
    Re-read all reports in .claude/reports/ and all registries in .claude/mlops/.
    Complete your validation and save your report."
3. After the retry, check again. If still missing, log a warning:
   "WARNING: mlops-engineer report missing after retry — proceeding without it."
```

### Stage 6: Streamlit Dashboard

#### Stage 6 Pre-Reflection (unless --no-pre-reflect)

Spawn **frontend-ux-analyst** in pre-reflection mode for dashboard. Reads all prior reports + lessons + frontend-ux-analyst recommendations. Saves plan to `stage_plan_dashboard.json`.

#### Step 6a: Dashboard Creation (Grounded — No Placeholders)

**Spawn developer agent** to create the dashboard. The prompt MUST include these rules:

```
Create an interactive Streamlit dashboard at dashboard/app.py.

CRITICAL RULES — read these before writing any code:
1. All variables MUST be defined before use. No undefined names like fig_overview, ml_mode, etc.
2. No placeholder strings like "{count}", "{value}", "{Project}", "{accuracy}". Use ACTUAL data.
3. BEFORE writing dashboard code, READ these reports for real values:
   - .claude/reports/eda-analyst_report.json — row count, column count, column names, stats
   - .claude/reports/feature-engineering-analyst_report.json — feature recommendations
   - .claude/reports/ml-theory-advisor_report.json — methodology notes
   - .claude/reports/frontend-ux-analyst_report.json — dashboard design recommendations
   - Any model evaluation reports in reports/ directory
   - Check models/ directory for trained model artifacts (*.joblib, *.pkl, *.pickle)
4. Load data with pd.read_csv() and compute metrics at runtime — do NOT hardcode stats.
5. Wrap model-specific sections in try/except or os.path.exists() checks so the
   dashboard works even if model artifacts are missing.
6. Every st.plotly_chart() call must use a figure created in the SAME scope.
7. Use st.set_page_config(page_title="Data Dashboard", layout="wide") at the top.
8. PLOTLY COLOR SAFETY: All color values MUST be valid CSS3 named colors, hex, or
   rgb/rgba strings. ONLY use colors from the W3C CSS3 list (147 named colors):
   e.g. "red", "green", "lightgray", "steelblue", "lightcoral", "tomato", "gold".
   Valid formats: named ("lightcoral"), hex ("#FF6347"), rgb ("rgb(255,99,71)"),
   rgba ("rgba(255,99,71,0.5)"). NEVER use: None, NaN, empty strings, variables
   that might be None, or invented color names not in the CSS3 spec.
   For go.Indicator gauge steps, always hardcode colors:
   gauge=dict(steps=[dict(range=[0,50], color="lightcoral"), dict(range=[50,100], color="lightgreen")])
   Reference: https://plotly.com/python/css-colors/

MODEL LOADING FOR LIVE INFERENCE:
9. Search for model artifacts: glob("models/*.joblib") + glob("models/*.pkl") + glob("models/*.pickle")
10. If a model artifact exists, load it with joblib.load() or pickle.load() in a try/except.
11. Also search for preprocessing pipeline artifacts (e.g. models/*pipeline*, models/*scaler*, models/*encoder*).
12. Store model availability in a boolean: HAS_MODEL = model is not None
13. Read feature names from the training report or model artifact (model.feature_names_in_ for sklearn).
14. For live inference: build input widgets matching each feature's type (st.number_input for numeric,
    st.selectbox for categorical with actual unique values from the dataset).
15. Show prediction result with confidence/probability when available (model.predict_proba).

DASHBOARD STRUCTURE (6 tabs):
- Sidebar: filters derived from actual categorical columns in the dataset.
  Include a "Reset Filters" button. Show dataset stats (row count, column count) in sidebar.
- Tab 1 (Overview): KPI metrics computed from df at runtime, summary charts, data quality gauge
- Tab 2 (EDA Deep Dive): ALL of these — distribution histograms for every numeric column,
  value counts bar charts for categoricals, correlation heatmap, missing value matrix,
  box plots for outlier detection, pairwise scatter plots for top correlated features,
  target variable analysis (class balance bar chart if classification)
- Tab 3 (Model Performance): If HAS_MODEL — confusion matrix heatmap, ROC curve, precision-recall
  curve, feature importance bar chart, model comparison table (if multiple models evaluated).
  If no model — show "No model trained yet" message with recommendations from theory advisor.
- Tab 4 (Live Inference): If HAS_MODEL — build a form with one widget per feature:
  * Numeric features: st.number_input with min/max/default from df.describe()
  * Categorical features: st.selectbox with actual unique values from df
  * Add "Predict" button. On click: preprocess inputs (apply same pipeline if available),
    run model.predict() and model.predict_proba(), display result prominently with
    st.metric for prediction and a gauge chart for confidence.
  * Show top feature contributions for this prediction if possible (use permutation importance
    or coefficient weights as approximation).
  If no model — show data explorer: column selector + filtered dataframe + download CSV button.
- Tab 5 (What-If Analysis): If HAS_MODEL — show sliders for top 5 most important features.
  As user adjusts sliders, re-run prediction in real-time. Display:
  * Current prediction + probability
  * A line/bar chart showing how the prediction changes as each feature varies across its range
  * Sensitivity table: for each feature, show prediction at min/25th/median/75th/max
  If no model — show segment comparison: pick a categorical column, compare distributions of
  numeric columns across segments with grouped box plots.
- Tab 6 (Data Explorer): Interactive data table with column search, sorting, download.
  Summary statistics table. Ability to filter rows by any column value.

Output: dashboard/app.py with all variables defined and no placeholders.
```

#### Step 6b: Dashboard Smoke Test (max 2 iterations)

After the developer agent writes `dashboard/app.py`, run this validation:

```python
import ast, re, importlib, sys

dashboard_path = "dashboard/app.py"
errors = []

# 1. Syntax check via ast.parse
with open(dashboard_path, "r") as f:
    source = f.read()
try:
    ast.parse(source)
except SyntaxError as e:
    errors.append(f"SyntaxError: {e}")

# 2. Unresolved placeholder check
placeholders = re.findall(r'"\{[^}]+\}"', source)
if placeholders:
    errors.append(f"Unresolved placeholders found: {placeholders}")

# 3. Import-level check (catches NameError/ImportError but tolerates Streamlit runtime)
if not errors:
    try:
        # Temporarily mock streamlit to avoid needing a running server
        import types
        mock_st = types.ModuleType("streamlit")
        sys.modules["streamlit"] = mock_st
        spec = importlib.util.spec_from_file_location("dashboard_check", dashboard_path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except (NameError, ImportError) as e:
            errors.append(f"Runtime error: {e}")
        except Exception:
            pass  # Tolerate other errors (Streamlit runtime, missing data, etc.)
        finally:
            sys.modules.pop("streamlit", None)
    except Exception as e:
        errors.append(f"Import test failed: {e}")

if errors:
    print("DASHBOARD VALIDATION FAILED:")
    for err in errors:
        print(f"  - {err}")
else:
    print("DASHBOARD VALIDATION PASSED")
```

**Iteration loop:**
```
iteration = 0
max_iterations = 2

while validation fails AND iteration < max_iterations:
  Re-spawn developer with:
    "DASHBOARD SMOKE TEST FAILED — fix these errors:
     {error_list}
     Read dashboard/app.py, fix the issues, and rewrite it.
     Remember: no placeholders, all variables must be defined, load real data."
  Run validation again
  iteration += 1

If still failing after max_iterations:
  Write a minimal fallback dashboard:
    - Loads data, shows df.describe(), basic bar chart
    - No model dependencies, no placeholders
  Log: "WARNING: Dashboard fell back to minimal version after {max_iterations} failed fixes"
```

**Output:**
```markdown
## Stage 6: Streamlit Dashboard ✓

- Dashboard created: dashboard/app.py
- Smoke test: PASSED (iteration {n})
- Tabs: Overview, EDA Deep Dive, Model Performance, Live Inference, What-If Analysis, Data Explorer
- Live inference: {enabled/disabled based on model availability}
- All variables grounded — no placeholders

### To Run Dashboard:
```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Dashboard URL: http://localhost:8501
PR #3: Merged ✓
```

### Stage 7: Productionalization

#### Stage 7 Pre-Reflection (unless --no-pre-reflect)

Spawn **mlops-engineer** in pre-reflection mode for production. Reads all prior reports + lessons. Saves plan to `stage_plan_production.json`.

**Actions:**
1. Invoke `mlops-engineer` to create production code
2. Create FastAPI endpoint (predictions for ML, data API for analysis)
3. Create Dockerfile with dashboard included
4. Generate integration tests
5. Create PR for production code
6. Invoke `brutal-code-reviewer` for review
7. Merge after approval

**Files to generate:**
- `api/app.py` - FastAPI application
- `api/schemas.py` - Pydantic models
- `dashboard/app.py` - Streamlit dashboard
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Service orchestration (API + Dashboard)

**Output:**
```markdown
## Stage 7: Productionalization ✓

- API created: api/app.py
- Dashboard created: dashboard/app.py
- Docker configured: Dockerfile
- Integration tests: 85% coverage
- PR #4: Merged ✓
- Production checklist: PASSED
```

### Stage 8: Deployment (Optional)

**If deployment requested:**

1. Determine target (local, snowflake, streamlit-sis, aws, gcp)
2. Invoke appropriate agent:
   - **Local**: `mlops-engineer` - Docker deployment
   - **Snowflake**: Deploy to Snowflake + Streamlit in Snowflake
   - **Cloud**: AWS/GCP deployment

3. Deploy both API and Dashboard
4. Verify health checks

**Output:**
```markdown
## Stage 8: Deployment ✓

- Target: local (or snowflake/aws/gcp)
- API deployed: http://localhost:8000
- Dashboard deployed: http://localhost:8501
- Health check: PASSED
```

### Stage 9: Finalization

**Actions:**
1. Generate comprehensive final report
2. Ensure all PRs merged to main
3. Update documentation
4. Close tasks
5. Output dashboard URL and access instructions

**Final Report:**
```markdown
## Project Complete: {Project Name}

### Summary
- Duration: {time}
- Mode: ML / Analysis
- PRs Merged: {count}
- Test Coverage: {percentage}%
- Key Metric: {value}

### Artifacts
- Data Pipeline: src/processing.py
- Model/Insights: src/model.py or src/insights.py
- API: http://localhost:8000
- Dashboard: http://localhost:8501

### Files Created
- src/processing.py
- src/model.py (ML) or src/insights.py (Analysis)
- api/app.py
- dashboard/app.py
- tests/unit/test_*.py
- tests/integration/test_api.py
- Dockerfile
- docker-compose.yml

### Dashboard Access
```bash
# Local development
streamlit run dashboard/app.py

# Docker
docker-compose up
# Dashboard: http://localhost:8501
# API: http://localhost:8000
```

### Lessons Learned
- Total lessons recorded: {count from load_lessons()}
- New lessons this run: {new_count}
- Most common issues: {top 3 by times_encountered}

### Next Steps
1. Review dashboard and customize visualizations
2. Share dashboard URL with stakeholders
3. Set up monitoring and alerts
4. Plan for data refresh schedule
```

## Error Handling

If any stage fails:
1. Log the error with context
2. Attempt automatic remediation if possible
3. Create an issue for manual intervention
4. Continue with remaining independent stages
5. Report partial completion status

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--target` | Auto-detect | Target variable name (triggers ML mode) |
| `--mode` | auto | Force mode: `ml` or `analysis` |
| `--no-deploy` | false | Skip deployment stage |
| `--deploy-to` | local | Deployment target (local, snowflake, aws, gcp) |
| `--dashboard-title` | Auto | Custom title for Streamlit dashboard |
| `--test-size` | 0.2 | Test split ratio (ML mode) |
| `--cv-folds` | 5 | Cross-validation folds (ML mode) |
| `--coverage-threshold` | 80 | Minimum test coverage |
| `--no-dashboard` | false | Skip dashboard creation |
| `--max-reflect` | 2 | Maximum reflection iterations per gate (0 to skip gates) |
| `--max-check` | 2 | Maximum self-check iterations per stage |
| `--no-pre-reflect` | false | Skip pre-stage reflection planning |
| `--no-lessons` | false | Skip lessons consultation |

## Dashboard Customization

The generated Streamlit dashboard includes:
- **Overview Tab**: KPI metrics, summary statistics
- **Analysis Tab**: EDA visualizations, distributions, correlations
- **Results Tab**: Model performance (ML) or key insights (Analysis)
- **Interactive Tab**: Predictions (ML) or data explorer (Analysis)

To customize after generation:
1. Edit `dashboard/app.py`
2. Add custom visualizations to `dashboard/components/`
3. Modify filters in sidebar
4. Run `streamlit run dashboard/app.py` to preview

## Agent Coordination

Throughout the workflow, agents are coordinated to:
- Track progress via task list
- Coordinate handoffs between stages
- Handle blockers and escalations
- Generate status updates

Invoke agents using the Task tool with appropriate prompts and context from previous stages.

## Output Structure

```
project/
├── src/
│   ├── processing.py      # Data processing pipeline
│   ├── model.py           # ML model (if ML mode)
│   └── insights.py        # Insights generation (if Analysis mode)
├── api/
│   ├── app.py             # FastAPI application
│   └── schemas.py         # Pydantic models
├── dashboard/
│   ├── app.py             # Streamlit dashboard
│   └── components/        # Reusable dashboard components
├── tests/
│   ├── unit/
│   └── integration/
├── reports/
│   ├── eda_report.md
│   └── final_report.md
├── models/                # Saved models (ML mode)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
