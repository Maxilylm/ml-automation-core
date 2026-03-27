# ml-automation-snowflake Extension Plugin Design

**Date:** 2026-03-27
**Status:** Draft
**Target Repo:** `Maxilylm/ml-automation-snowflake`

## Problem

Snowflake is a core platform for data engineering and ML at scale, but the ml-automation core plugin has no native Snowflake integration. Users need agents and commands for SQL development, Snowpark pipelines, Snowflake ML training, and deployment to Snowflake (model registry, Streamlit in Snowflake, stored procedures).

## Goal

Create `ml-automation-snowflake` as a self-contained Claude Code extension plugin that:
1. Follows the Extension Protocol (`extends: ml-automation`)
2. Hooks into core workflows at `after-init`, `before-deploy`, and `after-evaluation`
3. Provides full Snowflake development capabilities: SQL, Snowpark, ML, deployment
4. Manages Snowflake connection setup and credentials
5. Reuses core agents where appropriate

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Scope | Full: data engineering + ML + connector + deployment | Users want end-to-end Snowflake workflow |
| Connection pattern | Follows MMM `/ensure-bmmm-env` pattern | `/snowflake-connect` is Stage 0 prerequisite |
| Hook points | data-engineer→after-init, ml-engineer→before-deploy, reviewer→after-evaluation | Natural Snowflake integration points |
| Model tier | All agents use `sonnet` | Core uses generic tiers |
| Credentials | `~/.snowflake/connections.toml` + project overrides | Standard Snowflake Python connector pattern |

## Section 1: Plugin Manifest

```json
{
  "name": "ml-automation-snowflake",
  "version": "0.1.0",
  "description": "Snowflake development and ML automation extension for ml-automation. SQL development, Snowpark pipelines, Snowflake ML training, and deployment to Snowflake Model Registry and Streamlit in Snowflake.",
  "author": { "name": "Maximo Lorenzo y Losada" },
  "repository": "https://github.com/Maxilylm/ml-automation-snowflake",
  "license": "MIT",
  "keywords": ["snowflake", "snowpark", "snowflake-ml", "sql", "data-engineering", "ml-automation-extension", "streamlit-in-snowflake"],
  "dependencies": ["ml-automation-core"]
}
```

**Note:** `extends: ml-automation` lives in individual agent frontmatter, not in `plugin.json`. The `dependencies` array uses the format Claude Code expects.

## Section 2: Agent Definitions

### snowflake-data-engineer

```yaml
---
name: snowflake-data-engineer
description: "Snowflake SQL development, table design, data pipelines, Snowpark transformations, stages, streams, and tasks."
model: sonnet
color: "#29B5E8"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [snowflake sql, snowflake table, snowflake pipeline, snowpark, snowflake ddl, snowflake warehouse, snowflake stage, snowflake stream, snowflake task, snowflake view, snowflake schema]
hooks_into:
  - after-init
---
```

Relevance gate:
1. Check if `~/.snowflake/connections.toml` exists
2. Check if project has `.sql` files, `snowflake-connector-python` or `snowpark` in requirements
3. Check if data source references Snowflake tables (e.g., `SNOWFLAKE://` URIs, `from_table()` calls)
4. If NO Snowflake indicators: write skip report and exit
5. If Snowflake indicators found: set up connection, discover available data, report schema/tables

### snowflake-ml-engineer

```yaml
---
name: snowflake-ml-engineer
description: "Train models using Snowpark ML or Snowflake ML Functions. Register models in Snowflake Model Registry. Feature store integration."
model: sonnet
color: "#1B9CD0"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [snowpark ml, snowflake ml, snowflake model, snowflake train, snowflake feature store, snowflake ml functions, snowflake forecast, snowflake anomaly detection]
hooks_into:
  - before-deploy
---
```

Relevance gate: check for Snowflake connection + trained model artifacts. If found, offer Snowflake as deployment target.

### snowflake-reviewer

```yaml
---
name: snowflake-reviewer
description: "Validate SQL quality, Snowflake best practices, cost optimization, query performance, and Snowflake-compatibility of ML pipelines."
model: sonnet
color: "#0D7EAD"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [snowflake review, snowflake optimize, snowflake cost, snowflake best practices, snowflake query performance, snowflake audit]
hooks_into:
  - after-evaluation
---
```

Relevance gate: check for Snowflake artifacts (SQL files, Snowpark code, deployed models). If found, review for Snowflake-specific quality.

### snowflake-deployer

```yaml
---
name: snowflake-deployer
description: "Deploy models to Snowflake Model Registry, create Streamlit in Snowflake dashboards, set up stored procedures and UDFs for inference."
model: sonnet
color: "#056B91"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [snowflake deploy, streamlit in snowflake, snowflake stored procedure, snowflake udf, snowflake model registry, snowflake sis]
---
```

No hooks — invoked via `/snowflake-deploy` or by snowflake-ml-engineer.

### snowflake-connector

```yaml
---
name: snowflake-connector
description: "Snowflake connection management, credential setup, connection testing, data loading and unloading between Snowflake and local."
model: sonnet
color: "#38A1DB"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [snowflake connect, snowflake credentials, snowflake connection, snowflake auth, snowflake setup, snowflake config]
---
```

No hooks — invoked via `/snowflake-connect`.

## Section 3: Connection Management

### `/snowflake-connect` (Stage 0 prerequisite)

Following the MMM pattern where `/ensure-bmmm-env` manages the runtime environment:

1. Check if `~/.snowflake/connections.toml` exists
2. If exists — test connection with `SELECT CURRENT_VERSION()`, report status
3. If not — guide user through setup:
   - Account identifier, user, role, warehouse, database, schema
   - Auth method (password, key-pair, SSO/browser)
   - Write `connections.toml`
   - Test connection
4. Store project-specific overrides in `.claude/snowflake-config.json`:
   ```json
   {
     "connection_name": "default",
     "database": "MY_DB",
     "schema": "PUBLIC",
     "warehouse": "COMPUTE_WH",
     "role": "DATA_SCIENTIST"
   }
   ```

### Stage 0 Pattern (all Snowflake commands)

Every Snowflake command starts with:

```markdown
### Stage 0: Ensure Snowflake Connection

1. Check if `ml_utils.py` exists in `src/` — if missing, copy from core plugin
2. Check if `snowflake_utils.py` exists in `src/` — if missing, copy from this plugin's `templates/`
3. Run `/snowflake-connect --check` to verify connection is active
4. If connection fails, stop and tell user to run `/snowflake-connect`
```

## Section 4: Commands

### `/snowflake-coldstart` — Full Workflow

| Stage | Action | Agents Used |
|---|---|---|
| 0 | Ensure connection + utilities | snowflake-connector |
| 1 | Connect & discover — list databases, schemas, tables; profile source data | snowflake-data-engineer, eda-analyst (core) |
| 2 | SQL development — generate DDL for staging/feature tables, views | snowflake-data-engineer |
| 3 | Pipeline — build Snowpark transformation pipeline | snowflake-data-engineer, developer (core) |
| 4 | Train — Snowpark ML or Snowflake ML Functions | snowflake-ml-engineer, ml-theory-advisor (core) |
| 5 | Evaluate — model evaluation, results to Snowflake | snowflake-reviewer, developer (core) |
| 6 | Deploy — model registry, Streamlit in Snowflake, stored procedures | snowflake-deployer |
| 7 | Finalize — report, document deployed resources | snowflake-data-engineer |

### Individual Commands

| Command | Purpose | Key Agent |
|---|---|---|
| `/snowflake-connect` | Setup/test connection, write `connections.toml` | snowflake-connector |
| `/snowflake-sql` | Natural language → Snowflake SQL (DDL, DML, queries). Show for approval before execution | snowflake-data-engineer |
| `/snowflake-pipeline` | Build Snowpark DataFrame transformation pipeline. Reads EDA report if available | snowflake-data-engineer |
| `/snowflake-train` | Two modes: (a) Snowpark ML — sklearn-compatible in Snowpark, (b) Snowflake ML Functions — FORECAST, ANOMALY_DETECTION. Registers in Model Registry | snowflake-ml-engineer |
| `/snowflake-deploy` | Three targets: (a) Model Registry, (b) Streamlit in Snowflake, (c) Stored Procedure inference endpoint | snowflake-deployer |
| `/snowflake-migrate` | Convert existing Python ML code (pandas, sklearn) to Snowpark equivalents | snowflake-data-engineer |
| `/snowflake-status` | Query Snowflake metadata: warehouse usage, deployed models, Streamlit apps, stored procedures, recent queries | snowflake-connector |

## Section 5: snowflake_utils.py

```python
from ml_utils import save_agent_report, load_agent_report

def get_snowflake_connection(connection_name="default"):
    """Get Snowflake connection from connections.toml or project config."""
    ...

def execute_query(query, connection=None):
    """Execute a Snowflake SQL query and return results as list of dicts."""
    ...

def load_from_snowflake(query_or_table, connection=None):
    """Load data from Snowflake into a pandas DataFrame."""
    ...

def write_to_snowflake(df, table_name, database=None, schema=None, mode="append"):
    """Write a DataFrame to a Snowflake table."""
    ...

def get_snowpark_session(connection=None):
    """Create a Snowpark session for ML operations."""
    ...

def detect_snowflake_relevance(project_path="."):
    """Check if project has Snowflake indicators for relevance gating.

    Checks: connections.toml, .sql files, snowflake imports in requirements,
    Snowpark code patterns, SNOWFLAKE:// URIs.
    """
    ...

def get_snowflake_metadata(connection=None):
    """Query INFORMATION_SCHEMA for databases, schemas, tables, columns."""
    ...

def register_model_to_registry(model_path, model_name, version=None, connection=None):
    """Register a trained model in Snowflake Model Registry."""
    ...
```

**Distribution:** Same as MMM — commands copy `snowflake_utils.py` alongside `ml_utils.py` to the project's `src/` in Stage 0.

## Section 6: Report Bus Integration

| Agent | Report File |
|---|---|
| snowflake-data-engineer | `.claude/reports/snowflake-data-engineer_report.json` |
| snowflake-ml-engineer | `.claude/reports/snowflake-ml-engineer_report.json` |
| snowflake-reviewer | `.claude/reports/snowflake-reviewer_report.json` |
| snowflake-deployer | `.claude/reports/snowflake-deployer_report.json` |
| snowflake-connector | `.claude/reports/snowflake-connector_report.json` |

Snowflake-specific artifacts (SQL files, pipeline code, deployment configs) go to `snowflake/` in the user's project directory.

## Section 7: Plugin Directory Structure

```
ml-automation-snowflake/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── snowflake-data-engineer.md
│   ├── snowflake-ml-engineer.md
│   ├── snowflake-reviewer.md
│   ├── snowflake-deployer.md
│   └── snowflake-connector.md
├── skills/
│   ├── snowflake-connect/SKILL.md
│   ├── snowflake-coldstart/SKILL.md
│   ├── snowflake-sql/SKILL.md
│   ├── snowflake-pipeline/SKILL.md
│   ├── snowflake-train/SKILL.md
│   ├── snowflake-deploy/SKILL.md
│   ├── snowflake-migrate/SKILL.md
│   └── snowflake-status/SKILL.md
├── commands/
│   ├── snowflake-connect.md
│   ├── snowflake-coldstart.md
│   ├── snowflake-sql.md
│   ├── snowflake-pipeline.md
│   ├── snowflake-train.md
│   ├── snowflake-deploy.md
│   ├── snowflake-migrate.md
│   └── snowflake-status.md
├── templates/
│   └── snowflake_utils.py
└── hooks/
    └── hooks.json
```

## Section 8: Scope

### New Repository: `Maxilylm/ml-automation-snowflake`

1. Plugin manifest
2. 5 agents with Extension Protocol frontmatter and relevance gates
3. 8 skill definitions
4. 8 commands with Stage 0 connection checks
5. `snowflake_utils.py` — connection, query, load/write, Snowpark session, model registry
6. Empty `hooks.json`
7. README with installation and integration guide

### Marketplace Entry

Add to `ml-automation-plugin` marketplace:

```json
{
  "name": "ml-automation-snowflake",
  "description": "Snowflake development and ML automation extension. SQL development, Snowpark pipelines, ML training, and deployment to Snowflake.",
  "version": "0.1.0",
  "author": { "name": "Maximo Lorenzo y Losada" },
  "source": { "source": "url", "url": "https://github.com/Maxilylm/ml-automation-snowflake.git" },
  "category": "development",
  "homepage": "https://github.com/Maxilylm/ml-automation-snowflake",
  "dependencies": ["ml-automation-core"]
}
```
