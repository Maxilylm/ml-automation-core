"""
ml_utils.py — Reusable ML utilities for the ml-automation plugin.

Agents and skills should reference this file instead of regenerating common code.
Copy this file into your project's src/ directory at pipeline initialization.

Usage:
    from ml_utils import load_data, detect_column_types, build_preprocessor, evaluate_model
"""

import json
import os
from pathlib import Path

import pandas as pd


# =============================================================================
# 1. DATA LOADING
# =============================================================================

def load_data(path, **kwargs):
    """Load tabular data from CSV, Excel, JSON, or Parquet."""
    path = Path(path)
    loaders = {
        ".csv": pd.read_csv,
        ".tsv": lambda p, **kw: pd.read_csv(p, sep="\t", **kw),
        ".xlsx": pd.read_excel,
        ".xls": pd.read_excel,
        ".json": pd.read_json,
        ".parquet": pd.read_parquet,
        ".feather": pd.read_feather,
    }
    loader = loaders.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    return loader(path, **kwargs)


# =============================================================================
# 2. COLUMN TYPE DETECTION
# =============================================================================

def detect_column_types(df, target_col=None, id_threshold=0.95, cat_threshold=20):
    """
    Classify columns into numerical, categorical, datetime, text, and ID.

    Args:
        df: Input DataFrame
        target_col: Name of target column (excluded from feature lists)
        id_threshold: Uniqueness ratio above which a column is flagged as ID-like
        cat_threshold: Max unique values for a numeric column to be treated as categorical

    Returns:
        dict with keys: numerical, categorical, datetime, text, id_like, target
    """
    result = {
        "numerical": [],
        "categorical": [],
        "datetime": [],
        "text": [],
        "id_like": [],
        "target": target_col,
    }

    for col in df.columns:
        if col == target_col:
            continue

        dtype = df[col].dtype
        n_unique = df[col].nunique()
        uniqueness_ratio = n_unique / len(df) if len(df) > 0 else 0

        # ID-like detection
        if uniqueness_ratio > id_threshold and dtype == "object":
            result["id_like"].append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            result["datetime"].append(col)
        elif dtype == "object":
            avg_len = df[col].dropna().astype(str).str.len().mean()
            if avg_len > 50:
                result["text"].append(col)
            else:
                result["categorical"].append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            if n_unique <= cat_threshold:
                result["categorical"].append(col)
            else:
                result["numerical"].append(col)
        else:
            result["categorical"].append(col)

    return result


# =============================================================================
# 3. PREPROCESSING PIPELINE BUILDER
# =============================================================================

def build_preprocessor(numerical_cols, categorical_cols):
    """
    Build a sklearn ColumnTransformer with standard preprocessing.

    Returns a fitted-ready ColumnTransformer. Fit on TRAINING data only.
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    transformers = []
    if numerical_cols:
        transformers.append(("num", num_pipeline, numerical_cols))
    if categorical_cols:
        transformers.append(("cat", cat_pipeline, categorical_cols))

    return ColumnTransformer(transformers=transformers)


# =============================================================================
# 4. TRAIN-TEST SPLIT (LEAKAGE-SAFE)
# =============================================================================

def safe_split(df, target_col, test_size=0.2, random_state=42):
    """
    Split data into train/test BEFORE any preprocessing.

    For classification targets, uses stratified split.
    """
    from sklearn.model_selection import train_test_split

    X = df.drop(columns=[target_col])
    y = df[target_col]

    stratify = y if y.nunique() <= 20 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )
    return X_train, X_test, y_train, y_test


# =============================================================================
# 5. MODEL EVALUATION
# =============================================================================

def evaluate_model(model, X_test, y_test, problem_type="auto"):
    """
    Evaluate a model and return a metrics dictionary.

    Args:
        model: Fitted sklearn-compatible model
        X_test: Test features
        y_test: Test labels
        problem_type: 'classification', 'regression', or 'auto'

    Returns:
        dict of metric_name -> value
    """
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
        root_mean_squared_error, mean_absolute_error, r2_score,
    )

    y_pred = model.predict(X_test)

    if problem_type == "auto":
        problem_type = "classification" if y_test.nunique() <= 20 else "regression"

    metrics = {}

    if problem_type == "classification":
        metrics["accuracy"] = accuracy_score(y_test, y_pred)
        avg = "binary" if y_test.nunique() == 2 else "weighted"
        metrics["precision"] = precision_score(y_test, y_pred, average=avg, zero_division=0)
        metrics["recall"] = recall_score(y_test, y_pred, average=avg, zero_division=0)
        metrics["f1"] = f1_score(y_test, y_pred, average=avg, zero_division=0)
        if hasattr(model, "predict_proba"):
            try:
                y_proba = model.predict_proba(X_test)
                if y_test.nunique() == 2:
                    metrics["roc_auc"] = roc_auc_score(y_test, y_proba[:, 1])
                else:
                    metrics["roc_auc"] = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")
            except Exception:
                pass
    else:
        metrics["rmse"] = root_mean_squared_error(y_test, y_pred)
        metrics["mae"] = mean_absolute_error(y_test, y_pred)
        metrics["r2"] = r2_score(y_test, y_pred)

    return metrics


# =============================================================================
# 6. EDA REPORT I/O
# =============================================================================

def save_eda_report(report_data, output_dir=".claude"):
    """
    Save structured EDA report as JSON for downstream agents.
    Also saves in the new agent report bus format for v1.2.0+ compatibility.
    """
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "eda_report.json")
    with open(path, "w") as f:
        json.dump(report_data, f, indent=2, default=str)

    bus_report = {
        "status": "completed",
        "findings": {
            "summary": f"EDA completed: {report_data.get('shape', {}).get('rows', '?')} rows, {report_data.get('shape', {}).get('cols', '?')} columns",
            "details": report_data,
        },
        "recommendations": [],
        "next_steps": ["Run feature engineering", "Run ML theory review"],
        "artifacts": [path],
        "depends_on": [],
        "enables": ["feature-engineering-analyst", "ml-theory-advisor", "frontend-ux-analyst"],
    }
    for issue in report_data.get("quality_issues", []):
        bus_report["recommendations"].append({
            "action": f"Address {issue.get('issue', 'unknown')} in column {issue.get('column', '?')}",
            "priority": issue.get("severity", "medium"),
            "target_agent": "feature-engineering-analyst",
        })

    save_agent_report("eda-analyst", bus_report)
    return path


def load_eda_report(search_dirs=None):
    """
    Load prior EDA report if it exists.
    Checks both legacy .claude/eda_report.json and new bus format.
    """
    if search_dirs is None:
        search_dirs = [".claude", "reports", ".claude/reports", ".cursor/reports"]

    for d in search_dirs:
        path = os.path.join(d, "eda_report.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)

    reports = load_agent_reports(search_dirs)
    eda = reports.get("eda-analyst")
    if eda:
        return eda.get("findings", {}).get("details", eda.get("findings", {}))

    return None


def generate_eda_summary(df, target_col=None):
    """
    Generate a structured EDA summary dict suitable for saving and passing to agents.
    """
    col_types = detect_column_types(df, target_col=target_col)

    missing = {
        col: {"count": int(df[col].isnull().sum()), "pct": round(df[col].isnull().mean() * 100, 2)}
        for col in df.columns if df[col].isnull().sum() > 0
    }

    num_stats = {}
    for col in col_types["numerical"]:
        num_stats[col] = {
            "mean": round(float(df[col].mean()), 4),
            "median": round(float(df[col].median()), 4),
            "std": round(float(df[col].std()), 4),
            "min": round(float(df[col].min()), 4),
            "max": round(float(df[col].max()), 4),
            "skew": round(float(df[col].skew()), 4),
        }

    cat_stats = {}
    for col in col_types["categorical"]:
        cat_stats[col] = {
            "n_unique": int(df[col].nunique()),
            "top_values": df[col].value_counts().head(5).to_dict(),
        }

    # Correlation pairs > 0.8
    num_df = df[col_types["numerical"]]
    high_corr = []
    if len(num_df.columns) > 1:
        corr_matrix = num_df.corr()
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                val = corr_matrix.iloc[i, j]
                if abs(val) > 0.8:
                    high_corr.append({
                        "col_a": corr_matrix.columns[i],
                        "col_b": corr_matrix.columns[j],
                        "correlation": round(float(val), 4),
                    })

    return {
        "shape": {"rows": int(df.shape[0]), "cols": int(df.shape[1])},
        "column_types": col_types,
        "missing_values": missing,
        "numerical_stats": num_stats,
        "categorical_stats": cat_stats,
        "high_correlations": high_corr,
        "target": target_col,
        "quality_issues": _detect_quality_issues(df, col_types),
    }


def _detect_quality_issues(df, col_types):
    """Detect common data quality red flags."""
    issues = []

    for col in col_types["numerical"]:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        if series.nunique() == 1:
            issues.append({"column": col, "issue": "constant_value", "severity": "high"})
        elif abs(series.skew()) > 3:
            issues.append({"column": col, "issue": "highly_skewed", "severity": "medium", "skew": round(float(series.skew()), 2)})

    for col in col_types["categorical"]:
        series = df[col].dropna()
        if series.nunique() == 1:
            issues.append({"column": col, "issue": "constant_value", "severity": "high"})
        if series.nunique() > 100:
            issues.append({"column": col, "issue": "high_cardinality", "severity": "medium", "n_unique": int(series.nunique())})

    for col in df.columns:
        pct_missing = df[col].isnull().mean()
        if pct_missing > 0.5:
            issues.append({"column": col, "issue": "majority_missing", "severity": "high", "pct": round(pct_missing * 100, 1)})

    return issues


# =============================================================================
# 7. AGENT REPORT BUS
# =============================================================================

REPORT_SCHEMA_VERSION = "1.2.0"

PLATFORM_REPORT_DIRS = [".claude/reports", ".cursor/reports", ".codex/reports", ".opencode/reports", "reports"]


def save_agent_report(agent_name, report_data, output_dirs=None):
    """
    Save a standardized agent report to all platform report directories.

    Args:
        agent_name: The agent identifier (e.g., 'eda-analyst')
        report_data: Dict with keys: findings, recommendations, next_steps, artifacts
        output_dirs: List of directories to write to (defaults to all platform dirs)
    """
    from datetime import datetime, timezone

    if output_dirs is None:
        output_dirs = PLATFORM_REPORT_DIRS

    report = {
        "agent": agent_name,
        "version": REPORT_SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": report_data.get("status", "completed"),
        "findings": report_data.get("findings", {}),
        "recommendations": report_data.get("recommendations", []),
        "next_steps": report_data.get("next_steps", []),
        "artifacts": report_data.get("artifacts", []),
        "depends_on": report_data.get("depends_on", []),
        "enables": report_data.get("enables", []),
    }

    filename = f"{agent_name}_report.json"
    paths_written = []

    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, filename)
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        paths_written.append(path)

    return paths_written


def load_agent_reports(search_dirs=None):
    """
    Load all agent reports from report directories.

    Returns:
        dict of agent_name -> report_dict (most recent per agent)
    """
    import glob as globmod

    if search_dirs is None:
        search_dirs = PLATFORM_REPORT_DIRS

    reports = {}
    for d in search_dirs:
        pattern = os.path.join(d, "*_report.json")
        for filepath in globmod.glob(pattern):
            # Skip reflection reports — they have their own loader
            if "_reflection_" in os.path.basename(filepath):
                continue
            try:
                with open(filepath) as f:
                    report = json.load(f)
                agent = report.get("agent", os.path.basename(filepath).replace("_report.json", ""))
                if agent not in reports or report.get("timestamp", "") > reports[agent].get("timestamp", ""):
                    reports[agent] = report
            except (json.JSONDecodeError, KeyError):
                continue
    return reports


def get_workflow_status(search_dirs=None):
    """
    Get a summary of workflow status from agent reports.

    Returns:
        dict with keys: completed (list), pending (list), insights (list)
    """
    reports = load_agent_reports(search_dirs)

    # Build agent list dynamically from existing reports + known core agents
    core_agents = [
        "eda-analyst", "feature-engineering-analyst", "ml-theory-advisor",
        "frontend-ux-analyst", "developer", "brutal-code-reviewer",
        "pr-approver", "mlops-engineer", "orchestrator", "assigner",
    ]
    # Include any agent that has written a report (catches extension agents)
    discovered_agents = set(core_agents) | set(reports.keys())
    workflow_agents = sorted(discovered_agents)

    completed = []
    for agent_name, report in reports.items():
        summary = report.get("findings", {}).get("summary", "No summary")
        completed.append({"agent": agent_name, "summary": summary, "timestamp": report.get("timestamp", "")})

    completed_names = set(reports.keys())
    pending = [a for a in workflow_agents if a not in completed_names]

    insights = []
    for agent_name, report in reports.items():
        for rec in report.get("recommendations", []):
            if rec.get("target_agent") and rec.get("target_agent") not in completed_names:
                insights.append({
                    "from": agent_name,
                    "to": rec["target_agent"],
                    "action": rec.get("action", ""),
                    "priority": rec.get("priority", "medium"),
                })

    return {"completed": completed, "pending": pending, "insights": insights}


# =============================================================================
# 8. REFLECTION REPORTS
# =============================================================================

REFLECTION_GATES = ["post-feature-engineering", "post-preprocessing", "post-training"]


def save_reflection_report(gate, report_data, output_dirs=None):
    """
    Save a reflection gate report from ml-theory-advisor.

    Args:
        gate: One of 'post-feature-engineering', 'post-preprocessing', 'post-training'
        report_data: Dict with keys: verdict, reasoning, corrections
        output_dirs: List of directories (defaults to PLATFORM_REPORT_DIRS)
    """
    from datetime import datetime, timezone

    if output_dirs is None:
        output_dirs = PLATFORM_REPORT_DIRS

    report = {
        "agent": "ml-theory-advisor",
        "version": REPORT_SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "findings": {
            "summary": f"Reflection gate: {gate}",
            "details": {
                "gate": gate,
                "verdict": report_data.get("verdict", "approved"),
                "reasoning": report_data.get("reasoning", ""),
                "corrections": report_data.get("corrections", []),
            },
        },
        "recommendations": [
            {
                "target_agent": c.get("target_agent", ""),
                "action": c.get("recommendation", c.get("issue", "")),
                "priority": c.get("priority", "medium"),
            }
            for c in report_data.get("corrections", [])
        ],
        "next_steps": [],
        "artifacts": [],
        "depends_on": [],
        "enables": [],
    }

    filename = f"ml-theory-advisor_reflection_{gate}_report.json"
    paths_written = []

    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, filename)
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        paths_written.append(path)

    return paths_written


def load_reflection_report(gate, search_dirs=None):
    """
    Load the most recent reflection report for a specific gate.

    Args:
        gate: One of 'post-feature-engineering', 'post-preprocessing', 'post-training'
        search_dirs: Directories to search (defaults to PLATFORM_REPORT_DIRS)

    Returns:
        dict with verdict, reasoning, corrections — or None if not found
    """
    if search_dirs is None:
        search_dirs = PLATFORM_REPORT_DIRS

    filename = f"ml-theory-advisor_reflection_{gate}_report.json"
    latest = None

    for d in search_dirs:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    report = json.load(f)
                if latest is None or report.get("timestamp", "") > latest.get("timestamp", ""):
                    latest = report
            except (json.JSONDecodeError, KeyError):
                continue

    if latest:
        return latest.get("findings", {}).get("details", {})
    return None


# =============================================================================
# 9. MLOPS REGISTRY
# =============================================================================

PLATFORM_MLOPS_DIRS = [
    ".claude/mlops",
    ".cursor/mlops",
    ".codex/mlops",
    ".opencode/mlops",
    "mlops",
]

MLOPS_SCHEMA_VERSION = "1.0"

# Task-type specific required metrics
TASK_TYPE_METRICS = {
    "classification": ["accuracy", "precision", "recall", "f1", "auc_roc"],
    "regression": ["rmse", "mae", "r2"],
    "mmm": ["r2", "mape", "channel_roi", "channel_contribution"],
    "segmentation": ["silhouette_score", "n_clusters"],
    "time_series": ["rmse", "mae", "mape"],
}


def _load_registry(filename, search_dirs=None):
    """Load a registry JSON file, returning the most recently modified version."""
    if search_dirs is None:
        search_dirs = PLATFORM_MLOPS_DIRS

    latest = None
    latest_mtime = 0
    for d in search_dirs:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            try:
                mtime = os.path.getmtime(path)
                with open(path) as f:
                    data = json.load(f)
                if mtime > latest_mtime:
                    latest = data
                    latest_mtime = mtime
            except (json.JSONDecodeError, KeyError, OSError):
                continue
    return latest


def _save_registry(filename, data, output_dirs=None):
    """Save a registry JSON file to all platform directories."""
    if output_dirs is None:
        output_dirs = PLATFORM_MLOPS_DIRS

    paths_written = []
    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, filename)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        paths_written.append(path)
    return paths_written


# --- Model Registry ---

def save_model_entry(model_entry, output_dirs=None):
    """
    Register a trained model in the model registry.

    Args:
        model_entry: Dict with keys: model_id, name, task_type, algorithm,
            framework, metrics, hyperparameters, artifact_path,
            data_fingerprint, feature_set, training_experiment_id,
            rationale, tags, status (default: 'challenger')
    """
    from datetime import datetime, timezone

    registry = _load_registry("model-registry.json", output_dirs) or {
        "version": MLOPS_SCHEMA_VERSION,
        "models": [],
    }

    entry = {
        "model_id": model_entry.get("model_id", f"model_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"),
        "name": model_entry.get("name", "unnamed_model"),
        "task_type": model_entry.get("task_type", "regression"),
        "algorithm": model_entry.get("algorithm", ""),
        "framework": model_entry.get("framework", "scikit-learn"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": model_entry.get("status", "challenger"),
        "metrics": model_entry.get("metrics", {}),
        "hyperparameters": model_entry.get("hyperparameters", {}),
        "artifact_path": model_entry.get("artifact_path", ""),
        "data_fingerprint": model_entry.get("data_fingerprint", ""),
        "feature_set": model_entry.get("feature_set", []),
        "training_experiment_id": model_entry.get("training_experiment_id", ""),
        "predecessor_id": model_entry.get("predecessor_id"),
        "rationale": model_entry.get("rationale", {}),
        "tags": model_entry.get("tags", []),
    }

    # Deduplicate: update existing entry if model_id already registered
    existing_idx = next((i for i, m in enumerate(registry["models"]) if m.get("model_id") == entry["model_id"]), None)
    if existing_idx is not None:
        registry["models"][existing_idx] = entry
    else:
        registry["models"].append(entry)
    return _save_registry("model-registry.json", registry, output_dirs)


def load_model_registry(search_dirs=None):
    """Load the model registry. Returns dict with 'models' list or None."""
    return _load_registry("model-registry.json", search_dirs)


def get_champion_model(search_dirs=None):
    """Get the current champion model, or None."""
    registry = load_model_registry(search_dirs)
    if not registry:
        return None
    for model in registry.get("models", []):
        if model.get("status") == "champion":
            return model
    return None


def promote_model(model_id, search_dirs=None, output_dirs=None):
    """Promote a model to champion, archiving the current champion."""
    registry = _load_registry("model-registry.json", search_dirs) or {"version": MLOPS_SCHEMA_VERSION, "models": []}

    # Verify target model exists before archiving current champion
    if not any(m.get("model_id") == model_id for m in registry["models"]):
        return []

    for model in registry["models"]:
        if model["model_id"] == model_id:
            model["status"] = "champion"
        elif model.get("status") == "champion":
            model["status"] = "archived"

    return _save_registry("model-registry.json", registry, output_dirs)


# --- Feature Store ---

def save_feature_entries(features, output_dirs=None):
    """
    Register features in the feature store.

    Args:
        features: List of dicts, each with keys: feature_id, name, description,
            dtype, source_columns, transformation, transformation_params,
            created_by, domain, task_type_relevance, tags, statistics, leakage_risk
    """
    from datetime import datetime, timezone

    store = _load_registry("feature-store.json", output_dirs) or {
        "version": MLOPS_SCHEMA_VERSION,
        "features": [],
    }

    existing_ids = {f.get("feature_id") for f in store["features"]}
    now = datetime.now(timezone.utc).isoformat()

    for feat in features:
        fid = feat.get("feature_id", feat.get("name", "unknown"))
        if fid in existing_ids:
            # Update existing feature
            for i, existing in enumerate(store["features"]):
                if existing["feature_id"] == fid:
                    store["features"][i].update(feat)
                    store["features"][i]["updated_at"] = now
                    break
        else:
            entry = {
                "feature_id": fid,
                "name": feat.get("name", fid),
                "description": feat.get("description", ""),
                "dtype": feat.get("dtype", "unknown"),
                "source_columns": feat.get("source_columns", []),
                "transformation": feat.get("transformation", "raw"),
                "transformation_params": feat.get("transformation_params", {}),
                "created_at": now,
                "created_by": feat.get("created_by", "feature-engineering-analyst"),
                "domain": feat.get("domain", "general"),
                "task_type_relevance": feat.get("task_type_relevance", []),
                "tags": feat.get("tags", []),
                "statistics": feat.get("statistics", {}),
                "used_in_models": feat.get("used_in_models", []),
                "leakage_risk": feat.get("leakage_risk", "unknown"),
            }
            store["features"].append(entry)
            existing_ids.add(fid)  # track within batch to prevent duplicates

    return _save_registry("feature-store.json", store, output_dirs)


def load_feature_store(search_dirs=None):
    """Load the feature store. Returns dict with 'features' list or None."""
    return _load_registry("feature-store.json", search_dirs)


# --- Experiment Tracking ---

def save_experiment(experiment_data, output_dirs=None):
    """
    Save an experiment log for a training run.

    Args:
        experiment_data: Dict with keys: experiment_id, name, task_type,
            rationale, dataset, model, metrics, artifacts, notes
    """
    from datetime import datetime, timezone

    if output_dirs is None:
        output_dirs = PLATFORM_MLOPS_DIRS

    now = datetime.now(timezone.utc).isoformat()
    exp_id = experiment_data.get("experiment_id", f"exp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")

    experiment = {
        "experiment_id": exp_id,
        "name": experiment_data.get("name", "unnamed_experiment"),
        "created_at": now,
        "status": experiment_data.get("status", "completed"),
        "task_type": experiment_data.get("task_type", "regression"),
        "rationale": experiment_data.get("rationale", {}),
        "dataset": experiment_data.get("dataset", {}),
        "model": experiment_data.get("model", {}),
        "metrics": experiment_data.get("metrics", {}),
        "artifacts": experiment_data.get("artifacts", []),
        "notes": experiment_data.get("notes", ""),
        "registered_model_id": experiment_data.get("registered_model_id", ""),
    }

    filename = f"experiments/{exp_id}.json"
    paths_written = []
    for d in output_dirs:
        exp_dir = os.path.join(d, "experiments")
        os.makedirs(exp_dir, exist_ok=True)
        path = os.path.join(d, filename)
        with open(path, "w") as f:
            json.dump(experiment, f, indent=2, default=str)
        paths_written.append(path)
    return paths_written


def load_experiments(search_dirs=None):
    """Load all experiment logs. Returns list of experiment dicts."""
    import glob as globmod

    if search_dirs is None:
        search_dirs = PLATFORM_MLOPS_DIRS

    experiments = {}
    for d in search_dirs:
        pattern = os.path.join(d, "experiments", "*.json")
        for filepath in globmod.glob(pattern):
            try:
                with open(filepath) as f:
                    exp = json.load(f)
                exp_id = exp.get("experiment_id", os.path.basename(filepath))
                if exp_id not in experiments:
                    experiments[exp_id] = exp
            except (json.JSONDecodeError, KeyError):
                continue
    return list(experiments.values())


# --- Data Versioning ---

def save_data_version(data_version, output_dirs=None):
    """
    Save a data version fingerprint.

    Args:
        data_version: Dict with keys: fingerprint, source_path, rows, columns,
            column_schema, statistics_hash, detected_task_type
    """
    from datetime import datetime, timezone

    if output_dirs is None:
        output_dirs = PLATFORM_MLOPS_DIRS

    now = datetime.now(timezone.utc).isoformat()
    fingerprint = data_version.get("fingerprint", "unknown")
    short_fp = fingerprint.replace("sha256:", "")[:12]

    version = {
        "fingerprint": fingerprint,
        "created_at": now,
        "source_path": data_version.get("source_path", ""),
        "rows": data_version.get("rows", 0),
        "columns": data_version.get("columns", 0),
        "column_schema": data_version.get("column_schema", {}),
        "statistics_hash": data_version.get("statistics_hash", ""),
        "detected_task_type": data_version.get("detected_task_type", "unknown"),
        "used_in_experiments": data_version.get("used_in_experiments", []),
    }

    filename = f"data-versions/{short_fp}.json"
    paths_written = []
    for d in output_dirs:
        dv_dir = os.path.join(d, "data-versions")
        os.makedirs(dv_dir, exist_ok=True)
        path = os.path.join(d, filename)
        with open(path, "w") as f:
            json.dump(version, f, indent=2, default=str)
        paths_written.append(path)
    return paths_written


def compute_data_fingerprint(df):
    """
    Compute a SHA-256 fingerprint for a DataFrame.

    Uses sorted column names, dtypes, row count, and a sample hash.
    """
    import hashlib

    parts = []
    parts.append(str(sorted(df.columns.tolist())))
    parts.append(str([str(df[c].dtype) for c in sorted(df.columns)]))
    parts.append(str(len(df)))

    # Sample first and last rows for content identity
    sample_size = min(100, len(df))
    if len(df) > 0:
        head = df.head(sample_size).to_csv(index=False)
        tail = df.tail(sample_size).to_csv(index=False)
        parts.append(head)
        parts.append(tail)

    content = "|".join(parts)
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"


def load_data_versions(search_dirs=None):
    """Load all data version fingerprints. Returns list of version dicts."""
    import glob as globmod

    if search_dirs is None:
        search_dirs = PLATFORM_MLOPS_DIRS

    versions = {}
    for d in search_dirs:
        pattern = os.path.join(d, "data-versions", "*.json")
        for filepath in globmod.glob(pattern):
            try:
                with open(filepath) as f:
                    ver = json.load(f)
                fp = ver.get("fingerprint", os.path.basename(filepath))
                if fp not in versions:
                    versions[fp] = ver
            except (json.JSONDecodeError, KeyError):
                continue
    return list(versions.values())


# =============================================================================
# 10. LESSONS LEARNED
# =============================================================================

LESSONS_FILENAME = "lessons-learned.json"
LESSONS_SCHEMA_VERSION = "1.0"

PLATFORM_LESSONS_DIRS = [
    ".claude",
    ".cursor",
    ".codex",
    ".opencode",
]


def save_lesson(lesson_data, output_dirs=None):
    """
    Record a lesson learned. If a similar lesson exists (same stage + title substring match),
    increment times_encountered instead of creating a duplicate.

    Args:
        lesson_data: Dict with keys: stage, category (mistake|solution|pattern|tip),
            severity (high|medium|low), title, description, trigger, resolution,
            tags (list), applicable_to (list of command names)
    """
    from datetime import datetime, timezone

    if output_dirs is None:
        output_dirs = PLATFORM_LESSONS_DIRS

    now = datetime.now(timezone.utc)
    store = _load_lessons_store(output_dirs)

    title = lesson_data.get("title", "")
    stage = lesson_data.get("stage", "")

    # Deduplication: find existing lesson with same stage and overlapping title
    existing_idx = None
    for i, lesson in enumerate(store["lessons"]):
        if lesson.get("stage") == stage and (
            title.lower() in lesson.get("title", "").lower()
            or lesson.get("title", "").lower() in title.lower()
        ):
            existing_idx = i
            break

    if existing_idx is not None:
        store["lessons"][existing_idx]["times_encountered"] += 1
        store["lessons"][existing_idx]["last_encountered"] = now.isoformat()
        if lesson_data.get("resolution"):
            store["lessons"][existing_idx]["resolution"] = lesson_data["resolution"]
    else:
        lesson_id = f"lesson_{now.strftime('%Y%m%d_%H%M%S')}"
        entry = {
            "lesson_id": lesson_id,
            "created_at": now.isoformat(),
            "stage": stage,
            "category": lesson_data.get("category", "tip"),
            "severity": lesson_data.get("severity", "medium"),
            "title": title,
            "description": lesson_data.get("description", ""),
            "trigger": lesson_data.get("trigger", ""),
            "resolution": lesson_data.get("resolution", ""),
            "tags": lesson_data.get("tags", []),
            "times_encountered": 1,
            "last_encountered": now.isoformat(),
            "applicable_to": lesson_data.get("applicable_to", []),
        }
        store["lessons"].append(entry)

    _save_lessons_store(store, output_dirs)
    return store


def load_lessons(search_dirs=None):
    """Load all lessons from the lessons-learned store. Returns list of lesson dicts."""
    store = _load_lessons_store(search_dirs)
    return store.get("lessons", [])


def get_relevant_lessons(stage=None, tags=None, command=None, search_dirs=None):
    """
    Get lessons relevant to a specific stage, tags, or command.
    Returns list sorted by severity (high first) then frequency.
    """
    lessons = load_lessons(search_dirs)

    if stage:
        lessons = [l for l in lessons if l.get("stage") == stage or stage in l.get("tags", [])]

    if tags:
        tag_set = set(tags)
        lessons = [l for l in lessons if tag_set & set(l.get("tags", []))]

    if command:
        lessons = [l for l in lessons if not l.get("applicable_to") or command in l["applicable_to"]]

    severity_order = {"high": 0, "medium": 1, "low": 2}
    lessons.sort(key=lambda l: (
        severity_order.get(l.get("severity", "low"), 2),
        -(l.get("times_encountered", 0)),
    ))

    return lessons


def format_lessons_for_prompt(lessons, max_lessons=5):
    """Format lessons as a string suitable for including in agent prompts."""
    if not lessons:
        return ""

    lines = ["LESSONS FROM PRIOR RUNS (avoid these mistakes, follow these patterns):"]
    for lesson in lessons[:max_lessons]:
        category = lesson.get("category", "tip")
        title = lesson.get("title", "Unknown")
        resolution = lesson.get("resolution", "")
        times = lesson.get("times_encountered", 1)
        severity = lesson.get("severity", "medium")

        line = f"- [{severity.upper()}] ({category}) {title}"
        if resolution:
            line += f" → FIX: {resolution}"
        if times > 1:
            line += f" (encountered {times}x)"
        lines.append(line)

    return "\n".join(lines)


def _load_lessons_store(search_dirs=None):
    """Load the most recent lessons store across all platform directories."""
    if search_dirs is None:
        search_dirs = PLATFORM_LESSONS_DIRS

    latest = None
    latest_mtime = 0
    for d in search_dirs:
        path = os.path.join(d, LESSONS_FILENAME)
        if os.path.exists(path):
            try:
                mtime = os.path.getmtime(path)
                with open(path) as f:
                    data = json.load(f)
                if mtime > latest_mtime:
                    latest = data
                    latest_mtime = mtime
            except (json.JSONDecodeError, KeyError, OSError):
                continue

    return latest or {"version": LESSONS_SCHEMA_VERSION, "lessons": []}


def _save_lessons_store(store, output_dirs=None):
    """Save the lessons store to all platform directories."""
    if output_dirs is None:
        output_dirs = PLATFORM_LESSONS_DIRS

    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, LESSONS_FILENAME)
        with open(path, "w") as f:
            json.dump(store, f, indent=2, default=str)


# =============================================================================
# 11. STAGE VALIDATION (Iterative Self-Check)
# =============================================================================

STAGE_VALIDATORS = {
    "eda": "_validate_eda_output",
    "feature-engineering": "_validate_feature_engineering_output",
    "preprocessing": "_validate_preprocessing_output",
    "training": "_validate_training_output",
    "evaluation": "_validate_evaluation_output",
    "dashboard": "_validate_dashboard_output",
}


def validate_stage_output(stage, context=None):
    """
    Run stage-specific validation checks.

    Args:
        stage: Stage name (eda, feature-engineering, preprocessing, training, evaluation, dashboard)
        context: Optional dict with stage-specific context (e.g., file paths, data)

    Returns:
        tuple: (passed: bool, errors: list[str])
    """
    if context is None:
        context = {}

    validator_name = STAGE_VALIDATORS.get(stage)
    if validator_name is None:
        return True, []

    validator = globals().get(validator_name)
    if validator is None:
        return True, []

    return validator(context)


def _validate_eda_output(context):
    """Validate EDA stage output."""
    errors = []
    report = load_eda_report()

    if report is None:
        errors.append("EDA report not found in any report directory")
        return False, errors

    required_keys = ["shape", "column_types"]
    for key in required_keys:
        if key not in report:
            errors.append(f"EDA report missing required key: '{key}'")

    shape = report.get("shape", {})
    if not shape.get("rows") or not shape.get("cols"):
        errors.append("EDA report has empty or zero shape (rows/cols)")

    if not report.get("numerical_stats") and not report.get("categorical_stats"):
        errors.append("EDA report has no numerical or categorical statistics")

    if "quality_issues" not in report:
        errors.append("EDA report missing quality_issues assessment")

    return len(errors) == 0, errors


def _validate_feature_engineering_output(context):
    """Validate feature engineering output."""
    errors = []
    reports = load_agent_reports()
    fe_report = reports.get("feature-engineering-analyst")

    if fe_report is None:
        errors.append("Feature engineering report not found")
        return False, errors

    findings = fe_report.get("findings", {})
    details = findings.get("details", findings)

    features = []
    if isinstance(details, dict):
        features = details.get("features", details.get("recommended_features", []))
        if not features:
            errors.append("No features recommended in feature engineering report")

    # Check for duplicate feature IDs
    if features and isinstance(features, list):
        feature_ids = [f.get("feature_id", f.get("name", "")) for f in features if isinstance(f, dict)]
        duplicates = [fid for fid in feature_ids if feature_ids.count(fid) > 1]
        if duplicates:
            errors.append(f"Duplicate feature IDs: {list(set(duplicates))}")

        # Check leakage_risk is assessed
        missing_leakage = [
            f.get("feature_id", f.get("name", "?"))
            for f in features if isinstance(f, dict) and not f.get("leakage_risk")
        ]
        if missing_leakage:
            errors.append(f"Features missing leakage_risk assessment: {missing_leakage[:5]}")

    recs = fe_report.get("recommendations", [])
    if not recs and not features:
        errors.append("Feature engineering report has no recommendations or details")

    return len(errors) == 0, errors


def _validate_preprocessing_output(context):
    """Validate preprocessing stage output."""
    errors = []

    processing_paths = ["src/processing.py", "processing.py"]
    found = any(os.path.exists(p) for p in processing_paths)
    if not found:
        errors.append("Processing pipeline file not found (expected src/processing.py)")

    test_paths = ["tests/unit/test_processing.py", "tests/test_processing.py"]
    found_test = any(os.path.exists(p) for p in test_paths)
    if not found_test:
        errors.append("No test file found for processing pipeline")

    return len(errors) == 0, errors


def _validate_training_output(context):
    """Validate training stage output."""
    errors = []

    model_paths = ["models/", "src/models/"]
    import glob as globmod
    model_files = []
    for mp in model_paths:
        model_files.extend(globmod.glob(os.path.join(mp, "*.joblib")))
        model_files.extend(globmod.glob(os.path.join(mp, "*.pkl")))
        model_files.extend(globmod.glob(os.path.join(mp, "*.pickle")))
    if not model_files:
        errors.append("No model artifact found (expected .joblib or .pkl in models/)")

    experiments = load_experiments()
    if not experiments:
        errors.append("No experiment logged in MLOps registry")

    return len(errors) == 0, errors


def _validate_evaluation_output(context):
    """Validate evaluation stage output."""
    errors = []

    reports = load_agent_reports()
    has_eval = any("eval" in name.lower() or "theory" in name.lower() for name in reports)
    if not has_eval:
        import glob as globmod
        eval_files = globmod.glob("reports/*eval*") + globmod.glob("reports/*performance*")
        if not eval_files:
            errors.append("No evaluation report or metrics file found")

    return len(errors) == 0, errors


def _validate_dashboard_output(context):
    """Validate dashboard output (supplements the post-dashboard hook)."""
    import ast
    import re
    import glob as globmod

    errors = []
    warnings = []
    dashboard_path = context.get("dashboard_path", "dashboard/app.py")

    if not os.path.exists(dashboard_path):
        errors.append(f"Dashboard file not found: {dashboard_path}")
        return False, errors

    with open(dashboard_path) as f:
        source = f.read()

    try:
        ast.parse(source)
    except SyntaxError as e:
        errors.append(f"Dashboard syntax error: {e}")

    placeholders = re.findall(r'"\{[A-Za-z_][A-Za-z0-9_]*\}"', source)
    if placeholders:
        errors.append(f"Unresolved placeholders: {placeholders}")

    # Check for interactive features
    has_tabs = "st.tabs" in source
    has_model_loading = "joblib.load" in source or "pickle.load" in source
    has_inference = "predict(" in source or "predict_proba" in source
    has_input_widgets = any(
        w in source
        for w in ["st.number_input", "st.selectbox", "st.slider", "st.form"]
    )

    # Check if model artifacts exist — if so, dashboard should support inference
    model_files = (
        globmod.glob("models/*.joblib")
        + globmod.glob("models/*.pkl")
        + globmod.glob("models/*.pickle")
    )
    if model_files and not has_model_loading:
        warnings.append(
            "Model artifacts found but dashboard has no model loading — "
            "consider adding live inference"
        )
    if has_model_loading and not has_inference:
        warnings.append("Model is loaded but no predict() calls found")
    if has_model_loading and not has_input_widgets:
        warnings.append(
            "Model loaded but no input widgets (st.number_input, st.selectbox) "
            "for live inference"
        )
    if not has_tabs:
        warnings.append("Dashboard should use st.tabs for organized layout")

    # Attach warnings to errors list prefixed so callers can distinguish
    for w in warnings:
        errors.append(f"WARNING: {w}")

    # Only hard-fail on actual errors, not warnings
    hard_errors = [e for e in errors if not e.startswith("WARNING:")]
    return len(hard_errors) == 0, errors


# =============================================================================
# 12. PRE-STAGE PLANS
# =============================================================================

def save_stage_plan(stage, plan_data, output_dirs=None):
    """
    Save a pre-stage plan to the report bus directories.

    Args:
        stage: Stage name (e.g., 'analysis', 'preprocessing', 'training')
        plan_data: Dict with keys: stage, stage_number, objectives (list),
            approach (str), risks (list), success_criteria (list),
            lessons_applied (list), context_from_prior_stages (dict)
    """
    from datetime import datetime, timezone

    if output_dirs is None:
        output_dirs = PLATFORM_REPORT_DIRS

    plan = {
        "stage": stage,
        "stage_number": plan_data.get("stage_number", 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "objectives": plan_data.get("objectives", []),
        "approach": plan_data.get("approach", ""),
        "risks": plan_data.get("risks", []),
        "success_criteria": plan_data.get("success_criteria", []),
        "lessons_applied": plan_data.get("lessons_applied", []),
        "context_from_prior_stages": plan_data.get("context_from_prior_stages", {}),
    }

    filename = f"stage_plan_{stage}.json"
    paths_written = []

    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, filename)
        with open(path, "w") as f:
            json.dump(plan, f, indent=2, default=str)
        paths_written.append(path)

    return paths_written


def load_stage_plan(stage, search_dirs=None):
    """
    Load the pre-stage plan for a specific stage.

    Returns:
        dict with plan data, or None if not found
    """
    if search_dirs is None:
        search_dirs = PLATFORM_REPORT_DIRS

    filename = f"stage_plan_{stage}.json"

    for d in search_dirs:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                continue

    return None


# =============================================================================
# 13. TRACEABILITY LOG (Audit System)
# =============================================================================

TRACEABILITY_FILENAME = "traceability-log.jsonl"

PLATFORM_TRACE_DIRS = [
    ".claude",
    ".cursor",
    ".codex",
    ".opencode",
]


def log_trace_event(event_data, output_dirs=None):
    """
    Append a trace event to the traceability log (JSONL format).

    Args:
        event_data: Dict with keys:
            - event_type: 'agent_spawn' | 'agent_complete' | 'stage_start' | 'stage_end'
                          | 'decision' | 'reflection' | 'validation' | 'error' | 'user_action'
            - agent: Agent name (if applicable)
            - action: Brief description of what was done
            - details: Dict with event-specific data
            - inputs_summary: What the agent/action received
            - outputs_summary: What was produced
            - duration_ms: Execution time in milliseconds (if known)
            - stage: Pipeline stage name (if applicable)
            - command: Originating command (e.g., 'team-coldstart')
    """
    from datetime import datetime, timezone

    if output_dirs is None:
        output_dirs = PLATFORM_TRACE_DIRS

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_data.get("event_type", "unknown"),
        "agent": event_data.get("agent", ""),
        "action": event_data.get("action", ""),
        "details": event_data.get("details", {}),
        "inputs_summary": event_data.get("inputs_summary", ""),
        "outputs_summary": event_data.get("outputs_summary", ""),
        "duration_ms": event_data.get("duration_ms"),
        "stage": event_data.get("stage", ""),
        "command": event_data.get("command", ""),
    }

    line = json.dumps(entry, default=str)

    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, TRACEABILITY_FILENAME)
        with open(path, "a") as f:
            f.write(line + "\n")


def load_trace_log(search_dirs=None, filters=None):
    """
    Load and optionally filter the traceability log.

    Args:
        search_dirs: Directories to search (defaults to PLATFORM_TRACE_DIRS)
        filters: Optional dict with filter keys:
            - event_type: str or list of event types
            - agent: str agent name
            - stage: str stage name
            - command: str command name
            - since: ISO timestamp string — only events after this time
            - limit: int max entries to return (most recent first)

    Returns:
        List of trace event dicts, newest first.
    """
    if search_dirs is None:
        search_dirs = PLATFORM_TRACE_DIRS

    if filters is None:
        filters = {}

    entries = []
    seen_timestamps = set()

    for d in search_dirs:
        path = os.path.join(d, TRACEABILITY_FILENAME)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            ts = entry.get("timestamp", "")
                            key = f"{ts}_{entry.get('event_type', '')}_{entry.get('agent', '')}"
                            if key not in seen_timestamps:
                                seen_timestamps.add(key)
                                entries.append(entry)
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue

    # Apply filters
    event_type_filter = filters.get("event_type")
    if event_type_filter:
        if isinstance(event_type_filter, str):
            event_type_filter = [event_type_filter]
        entries = [e for e in entries if e.get("event_type") in event_type_filter]

    for key in ("agent", "stage", "command"):
        val = filters.get(key)
        if val:
            entries = [e for e in entries if e.get(key) == val]

    since = filters.get("since")
    if since:
        entries = [e for e in entries if e.get("timestamp", "") >= since]

    # Sort newest first
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    limit = filters.get("limit")
    if limit:
        entries = entries[:limit]

    return entries


def format_trace_log(entries, verbose=False):
    """Format trace log entries for display."""
    if not entries:
        return "No trace events found."

    lines = [f"TRACEABILITY LOG ({len(entries)} events)\n"]
    for entry in entries:
        ts = entry.get("timestamp", "?")[:19].replace("T", " ")
        event_type = entry.get("event_type", "?")
        agent = entry.get("agent", "")
        action = entry.get("action", "")
        stage = entry.get("stage", "")

        icon = {
            "agent_spawn": "→",
            "agent_complete": "✓",
            "stage_start": "▶",
            "stage_end": "■",
            "decision": "◆",
            "reflection": "◈",
            "validation": "✔",
            "error": "✗",
            "user_action": "●",
        }.get(event_type, "·")

        line = f"  {icon} [{ts}] {event_type}"
        if agent:
            line += f" | {agent}"
        if stage:
            line += f" | stage:{stage}"
        if action:
            line += f" — {action}"
        lines.append(line)

        if verbose:
            if entry.get("inputs_summary"):
                lines.append(f"      IN:  {entry['inputs_summary']}")
            if entry.get("outputs_summary"):
                lines.append(f"      OUT: {entry['outputs_summary']}")
            if entry.get("duration_ms"):
                lines.append(f"      Duration: {entry['duration_ms']}ms")

    return "\n".join(lines)


# =============================================================================
# 14. BUSINESS PLAUSIBILITY CHECKS
# =============================================================================

DEFAULT_PLAUSIBILITY_RULES = {
    "coefficient_sign": {
        "description": "Check that model coefficients have expected signs",
        "enabled": True,
    },
    "prediction_range": {
        "description": "Check predictions fall within plausible domain range",
        "enabled": True,
    },
    "effect_size": {
        "description": "Check ROAS/effect sizes are within plausible bounds",
        "enabled": True,
        "roas_min": 0.1,
        "roas_max": 50.0,
    },
    "feature_importance_sanity": {
        "description": "Check top features match domain expectations",
        "enabled": True,
    },
    "prediction_distribution": {
        "description": "Check prediction distribution is not degenerate",
        "enabled": True,
        "min_unique_ratio": 0.01,
    },
}


def validate_business_plausibility(context, config=None):
    """
    Run business plausibility checks on model outputs.

    Args:
        context: Dict with available keys:
            - model: Fitted model object
            - X_test: Test features DataFrame
            - y_test: Test target Series
            - y_pred: Predictions array
            - feature_names: List of feature names
            - feature_importances: Dict of feature_name -> importance
            - task_type: 'classification' | 'regression' | 'mmm'
            - domain_expectations: Dict with domain-specific rules:
                - expected_positive_features: list
                - expected_negative_features: list
                - target_min: minimum plausible target value
                - target_max: maximum plausible target value
                - top_features_expected: list of features expected to be important
            - roas_values: Dict of channel -> ROAS (for MMM)

        config: Optional plausibility rules config dict

    Returns:
        dict: passed (bool), checks (list), summary (str), critical_failures (int)
    """
    import numpy as np

    if config is None:
        config = _load_plausibility_config()

    checks = []
    critical_failures = 0

    # --- Check 1: Coefficient sign plausibility ---
    if config.get("coefficient_sign", {}).get("enabled", True):
        model = context.get("model")
        domain = context.get("domain_expectations", {})
        pos_features = domain.get("expected_positive_features", [])
        neg_features = domain.get("expected_negative_features", [])

        if model and hasattr(model, "coef_") and (pos_features or neg_features):
            feature_names = context.get("feature_names", [])
            coefs = model.coef_.flatten() if hasattr(model.coef_, "flatten") else model.coef_
            coef_dict = dict(zip(feature_names, coefs)) if len(feature_names) == len(coefs) else {}

            violations = []
            for feat in pos_features:
                if feat in coef_dict and coef_dict[feat] < 0:
                    violations.append(f"{feat} expected positive, got {coef_dict[feat]:.4f}")
            for feat in neg_features:
                if feat in coef_dict and coef_dict[feat] > 0:
                    violations.append(f"{feat} expected negative, got {coef_dict[feat]:.4f}")

            check = {
                "name": "coefficient_sign",
                "passed": len(violations) == 0,
                "severity": "high",
                "details": violations if violations else "All coefficient signs match expectations",
            }
            checks.append(check)
            if not check["passed"]:
                critical_failures += 1
        else:
            checks.append({
                "name": "coefficient_sign",
                "passed": True,
                "severity": "info",
                "details": "Skipped — no linear model or no domain expectations provided",
            })

    # --- Check 2: Prediction range plausibility ---
    if config.get("prediction_range", {}).get("enabled", True):
        y_pred = context.get("y_pred")
        domain = context.get("domain_expectations", {})
        target_min = domain.get("target_min")
        target_max = domain.get("target_max")

        if y_pred is not None and (target_min is not None or target_max is not None):
            pred_arr = np.asarray(y_pred)
            violations = []
            if target_min is not None and pred_arr.min() < target_min:
                violations.append(f"Min prediction {pred_arr.min():.4f} < domain min {target_min}")
            if target_max is not None and pred_arr.max() > target_max:
                violations.append(f"Max prediction {pred_arr.max():.4f} > domain max {target_max}")

            pct_out = 0
            if target_min is not None and target_max is not None:
                out_of_range = ((pred_arr < target_min) | (pred_arr > target_max)).sum()
                pct_out = out_of_range / len(pred_arr) * 100

            check = {
                "name": "prediction_range",
                "passed": len(violations) == 0,
                "severity": "high" if pct_out > 10 else "medium",
                "details": violations if violations else "All predictions within expected range",
                "pct_out_of_range": round(pct_out, 2),
            }
            checks.append(check)
            if not check["passed"] and check["severity"] == "high":
                critical_failures += 1
        else:
            checks.append({
                "name": "prediction_range",
                "passed": True,
                "severity": "info",
                "details": "Skipped — no predictions or domain bounds provided",
            })

    # --- Check 3: ROAS/Effect size plausibility ---
    if config.get("effect_size", {}).get("enabled", True):
        roas_values = context.get("roas_values", {})
        roas_min = config.get("effect_size", {}).get("roas_min", 0.1)
        roas_max = config.get("effect_size", {}).get("roas_max", 50.0)

        if roas_values:
            violations = []
            for channel, roas in roas_values.items():
                if roas < roas_min:
                    violations.append(f"{channel}: ROAS {roas:.2f} < min {roas_min}")
                elif roas > roas_max:
                    violations.append(f"{channel}: ROAS {roas:.2f} > max {roas_max} (suspiciously high)")

            check = {
                "name": "effect_size",
                "passed": len(violations) == 0,
                "severity": "high",
                "details": violations if violations else f"All ROAS values within [{roas_min}, {roas_max}]",
            }
            checks.append(check)
            if not check["passed"]:
                critical_failures += 1
        else:
            checks.append({
                "name": "effect_size",
                "passed": True,
                "severity": "info",
                "details": "Skipped — no ROAS values provided",
            })

    # --- Check 4: Feature importance sanity ---
    if config.get("feature_importance_sanity", {}).get("enabled", True):
        importances = context.get("feature_importances", {})
        domain = context.get("domain_expectations", {})
        expected_top = domain.get("top_features_expected", [])

        if importances and expected_top:
            sorted_features = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)
            actual_top = [f[0] for f in sorted_features[:len(expected_top) * 2]]
            missing = [f for f in expected_top if f not in actual_top]

            check = {
                "name": "feature_importance_sanity",
                "passed": len(missing) == 0,
                "severity": "medium",
                "details": f"Expected important features not in top: {missing}" if missing
                    else "Top features match domain expectations",
                "actual_top_features": actual_top[:10],
            }
            checks.append(check)
        else:
            checks.append({
                "name": "feature_importance_sanity",
                "passed": True,
                "severity": "info",
                "details": "Skipped — no importances or expected features provided",
            })

    # --- Check 5: Prediction distribution sanity ---
    if config.get("prediction_distribution", {}).get("enabled", True):
        y_pred = context.get("y_pred")
        min_unique_ratio = config.get("prediction_distribution", {}).get("min_unique_ratio", 0.01)

        if y_pred is not None:
            pred_arr = np.asarray(y_pred)
            n_unique = len(np.unique(pred_arr))
            unique_ratio = n_unique / len(pred_arr) if len(pred_arr) > 0 else 0

            issues = []
            if n_unique == 1:
                issues.append("Degenerate predictions — model outputs a single constant value")
            elif unique_ratio < min_unique_ratio and context.get("task_type") != "classification":
                issues.append(f"Very low prediction diversity: {n_unique} unique values out of {len(pred_arr)}")

            check = {
                "name": "prediction_distribution",
                "passed": len(issues) == 0,
                "severity": "high" if n_unique == 1 else "medium",
                "details": issues if issues else "Prediction distribution looks reasonable",
                "n_unique_predictions": n_unique,
            }
            checks.append(check)
            if not check["passed"] and check["severity"] == "high":
                critical_failures += 1

    # Build summary
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    failed = [c for c in checks if not c["passed"]]

    summary_lines = [f"Plausibility: {passed_count}/{total} checks passed"]
    for f in failed:
        summary_lines.append(f"  FAIL [{f['severity']}] {f['name']}: {f['details']}")

    return {
        "passed": critical_failures == 0,
        "checks": checks,
        "summary": "\n".join(summary_lines),
        "critical_failures": critical_failures,
    }


def _load_plausibility_config(search_dirs=None):
    """Load plausibility config from project or return defaults."""
    if search_dirs is None:
        search_dirs = PLATFORM_REPORT_DIRS

    for d in search_dirs:
        config_path = os.path.join(os.path.dirname(d), "plausibility_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
    return DEFAULT_PLAUSIBILITY_RULES


def save_plausibility_report(result, output_dirs=None):
    """Save plausibility check results as an agent report."""
    report_data = {
        "status": "completed",
        "findings": {
            "summary": result["summary"],
            "details": {
                "passed": result["passed"],
                "checks": result["checks"],
                "critical_failures": result["critical_failures"],
            },
        },
        "recommendations": [
            {
                "action": f"Review failed check: {c['name']} — {c['details']}",
                "target_agent": "ml-theory-advisor",
                "priority": c["severity"],
            }
            for c in result["checks"] if not c["passed"]
        ],
        "next_steps": ["Review failed checks with domain expert"] if not result["passed"] else [],
        "artifacts": [],
    }
    return save_agent_report("plausibility-validator", report_data, output_dirs)


# =============================================================================
# 15. DATABASE CONNECTORS
# =============================================================================

def load_data_from_db(connection_string, query, **kwargs):
    """
    Load data from a database into a DataFrame.

    Supports Snowflake, PostgreSQL, BigQuery, and any SQLAlchemy-compatible database.

    Args:
        connection_string: Database URI string or dict with connection params.
            - Snowflake: 'snowflake://user:pass@account/db/schema?warehouse=WH'
            - PostgreSQL: 'postgresql://user:pass@host:port/db'
            - BigQuery: 'bigquery://project/dataset'
            - Dict: {type: 'snowflake'|'bigquery'|'postgresql', ...connection params}
        query: SQL query string or table name
        **kwargs: Additional arguments passed to pd.read_sql()

    Returns:
        pandas DataFrame
    """
    if isinstance(connection_string, dict):
        return _load_from_db_config(connection_string, query, **kwargs)

    conn_lower = connection_string.lower()

    if conn_lower.startswith("snowflake://"):
        return _load_from_snowflake_uri(connection_string, query, **kwargs)
    elif conn_lower.startswith("bigquery://"):
        return _load_from_bigquery_uri(connection_string, query, **kwargs)
    else:
        return _load_from_sqlalchemy(connection_string, query, **kwargs)


def _load_from_db_config(config, query, **kwargs):
    """Load data using a config dict with explicit type field."""
    db_type = config.get("type", "").lower()

    if db_type == "snowflake":
        account = config.get("account", os.environ.get("SNOWFLAKE_ACCOUNT", ""))
        user = config.get("user", os.environ.get("SNOWFLAKE_USER", ""))
        password = config.get("password", os.environ.get("SNOWFLAKE_PASSWORD", ""))
        database = config.get("database", os.environ.get("SNOWFLAKE_DATABASE", ""))
        schema = config.get("schema", os.environ.get("SNOWFLAKE_SCHEMA", ""))
        warehouse = config.get("warehouse", os.environ.get("SNOWFLAKE_WAREHOUSE", ""))
        uri = f"snowflake://{user}:{password}@{account}/{database}/{schema}?warehouse={warehouse}"
        return _load_from_snowflake_uri(uri, query, **kwargs)

    elif db_type == "bigquery":
        project = config.get("project", os.environ.get("BIGQUERY_PROJECT", ""))
        credentials_path = config.get("credentials_path", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""))
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        uri = f"bigquery://{project}"
        return _load_from_bigquery_uri(uri, query, **kwargs)

    elif db_type in ("postgresql", "postgres", "pg"):
        host = config.get("host", os.environ.get("PGHOST", "localhost"))
        port = config.get("port", os.environ.get("PGPORT", "5432"))
        user = config.get("user", os.environ.get("PGUSER", ""))
        password = config.get("password", os.environ.get("PGPASSWORD", ""))
        database = config.get("database", os.environ.get("PGDATABASE", ""))
        uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return _load_from_sqlalchemy(uri, query, **kwargs)

    else:
        raise ValueError(f"Unsupported database type: {db_type}. Use 'snowflake', 'bigquery', or 'postgresql'.")


def _load_from_snowflake_uri(uri, query, **kwargs):
    """Load data from Snowflake using snowflake-sqlalchemy."""
    try:
        from sqlalchemy import create_engine
    except ImportError:
        raise ImportError("Install sqlalchemy and snowflake-sqlalchemy: pip install sqlalchemy snowflake-sqlalchemy")

    engine = create_engine(uri)
    try:
        return pd.read_sql(query, engine, **kwargs)
    finally:
        engine.dispose()


def _load_from_bigquery_uri(uri, query, **kwargs):
    """Load data from BigQuery."""
    try:
        import pandas_gbq
    except ImportError:
        raise ImportError("Install pandas-gbq: pip install pandas-gbq")

    project = uri.replace("bigquery://", "").split("/")[0]
    return pandas_gbq.read_gbq(query, project_id=project, **kwargs)


def _load_from_sqlalchemy(uri, query, **kwargs):
    """Load data using SQLAlchemy (PostgreSQL, MySQL, SQLite, etc.)."""
    try:
        from sqlalchemy import create_engine
    except ImportError:
        raise ImportError("Install sqlalchemy: pip install sqlalchemy")

    engine = create_engine(uri)
    try:
        return pd.read_sql(query, engine, **kwargs)
    finally:
        engine.dispose()
