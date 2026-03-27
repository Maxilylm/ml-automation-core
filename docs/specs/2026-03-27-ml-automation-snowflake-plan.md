# ml-automation-snowflake Extension Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `ml-automation-snowflake` Claude Code extension plugin — 5 agents, 8 skills/commands, connection management, and Snowflake ML automation following the Extension Protocol.

**Architecture:** New repo scaffolded as a Claude Code plugin. Agents declare `extends: ml-automation` with hook points. Connection follows the MMM pattern (Stage 0 prerequisite). Commands cover SQL development, Snowpark pipelines, ML training, and deployment to Snowflake.

**Tech Stack:** Markdown (agents, skills, commands), Python (snowflake_utils.py), JSON (plugin manifest, hooks)

**Spec:** `docs/specs/2026-03-27-ml-automation-snowflake-extension-design.md`

**Working directory:** `~/Documents/ml-automation-snowflake/`

**Prerequisites:**
- Core plugin v1.8.0 on `ml-automation-core` repo (done)
- MMM extension as structural template (done at `~/Documents/ml-automation-mmm/`)

---

### Task 1: Initialize Repository and Plugin Manifest

**Files:**
- Create: `~/Documents/ml-automation-snowflake/.claude-plugin/plugin.json`
- Create: `~/Documents/ml-automation-snowflake/.gitignore`

- [ ] **Step 1: Create directory and init git**

```bash
mkdir -p ~/Documents/ml-automation-snowflake
cd ~/Documents/ml-automation-snowflake
git init
```

- [ ] **Step 2: Create plugin manifest**

`.claude-plugin/plugin.json`:
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

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.idea/
.vscode/
*.swp
.DS_Store
Thumbs.db
reports/
models/
.venv/
```

- [ ] **Step 4: Create directory structure**

```bash
mkdir -p agents skills commands templates hooks
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: initialize ml-automation-snowflake plugin scaffold"
```

---

### Task 2: Create the 5 Agent Definitions

**Files:**
- Create: `~/Documents/ml-automation-snowflake/agents/snowflake-data-engineer.md`
- Create: `~/Documents/ml-automation-snowflake/agents/snowflake-ml-engineer.md`
- Create: `~/Documents/ml-automation-snowflake/agents/snowflake-reviewer.md`
- Create: `~/Documents/ml-automation-snowflake/agents/snowflake-deployer.md`
- Create: `~/Documents/ml-automation-snowflake/agents/snowflake-connector.md`

- [ ] **Step 1: Create snowflake-data-engineer.md**

```markdown
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

# Snowflake Data Engineer

## Relevance Gate (when running at a hook point)

When invoked at a core workflow hook point (not via direct command):
1. Check if `~/.snowflake/connections.toml` exists
2. Check if project has `.sql` files, or `snowflake-connector-python`/`snowpark` in requirements
3. Check if data source references Snowflake tables
4. If NO Snowflake indicators found — write skip report and exit:
   ```python
   from ml_utils import save_agent_report
   save_agent_report("snowflake-data-engineer", {
       "status": "skipped",
       "reason": "No Snowflake indicators found in project"
   })
   ```
5. If Snowflake indicators found: set up connection, discover schemas/tables, report available data

## Capabilities

- Generate Snowflake-optimized DDL (CREATE TABLE, VIEW, STAGE, STREAM, TASK)
- Design table schemas with clustering keys, data types, and partitioning
- Build Snowpark DataFrame transformation pipelines
- Create data loading pipelines (COPY INTO, Snowpipe)
- Optimize SQL queries for Snowflake architecture (micro-partitions, pruning)
- Generate stored procedures and UDFs

## Report Bus

Write report using `save_agent_report("snowflake-data-engineer", {...})` with:
- Discovered schemas and tables
- Generated SQL artifacts
- Pipeline configuration
- Performance recommendations
```

- [ ] **Step 2: Create snowflake-ml-engineer.md**

```markdown
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

# Snowflake ML Engineer

## Relevance Gate (when running at a hook point)

When invoked at `before-deploy` in a core workflow:
1. Check if Snowflake connection is configured
2. Check if trained model artifacts exist
3. If both present: offer Snowflake as deployment target (Model Registry, Streamlit in Snowflake)
4. If not: write skip report and exit

## Capabilities

### Snowpark ML
- Train sklearn-compatible models inside Snowpark
- Feature engineering with Snowpark DataFrames
- Distributed training with Snowpark ML

### Snowflake ML Functions
- Built-in FORECAST for time series
- ANOMALY_DETECTION for outlier detection
- CONTRIBUTION_EXPLORER for feature attribution

### Model Registry
- Register models in Snowflake Model Registry
- Version management
- Model lineage tracking

## Report Bus

Write report with: training metrics, model location, registry entry, deployment recommendations
```

- [ ] **Step 3: Create snowflake-reviewer.md**

```markdown
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

# Snowflake Reviewer

## Relevance Gate (when running at a hook point)

When invoked at `after-evaluation`:
1. Check for Snowflake artifacts (SQL files, Snowpark code, deployed models)
2. If none found: write skip report and exit
3. If found: review for Snowflake-specific quality

## Review Checklist

### SQL Quality
- Proper use of clustering keys
- Efficient JOIN patterns for Snowflake
- Appropriate warehouse sizing references
- No anti-patterns (SELECT *, unnecessary ORDER BY in subqueries)

### Cost Optimization
- Warehouse auto-suspend/resume settings
- Query complexity vs. warehouse size
- Materialized view vs. table trade-offs
- Storage optimization (transient vs. permanent tables)

### ML Pipeline Compatibility
- Snowpark ML API usage correctness
- Model Registry best practices
- Feature store integration patterns
- Inference stored procedure design

## Report Bus

Write report with: pass/fail checklist, cost estimates, optimization recommendations
```

- [ ] **Step 4: Create snowflake-deployer.md**

```markdown
---
name: snowflake-deployer
description: "Deploy models to Snowflake Model Registry, create Streamlit in Snowflake dashboards, set up stored procedures and UDFs for inference."
model: sonnet
color: "#056B91"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [snowflake deploy, streamlit in snowflake, snowflake stored procedure, snowflake udf, snowflake model registry, snowflake sis]
---

# Snowflake Deployer

No hooks — invoked via `/snowflake-deploy` or by snowflake-ml-engineer.

## Deployment Targets

### 1. Snowflake Model Registry
- Register trained model with version
- Set metadata (metrics, description, tags)
- Promote to production stage

### 2. Streamlit in Snowflake
- Generate Streamlit app code
- Deploy to Snowflake account
- Configure access and sharing

### 3. Stored Procedure / UDF
- Create inference stored procedure
- Package model dependencies
- Set up scheduling (Snowflake Tasks) for batch inference

## Report Bus

Write report with: deployment target, endpoint details, access configuration
```

- [ ] **Step 5: Create snowflake-connector.md**

```markdown
---
name: snowflake-connector
description: "Snowflake connection management, credential setup, connection testing, data loading and unloading between Snowflake and local."
model: sonnet
color: "#38A1DB"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [snowflake connect, snowflake credentials, snowflake connection, snowflake auth, snowflake setup, snowflake config]
---

# Snowflake Connector

No hooks — invoked via `/snowflake-connect`.

## Connection Management

### Setup Flow
1. Check for `~/.snowflake/connections.toml`
2. If missing: guide user through account, user, role, warehouse, database, schema, auth method
3. Write `connections.toml` in TOML format
4. Test with `SELECT CURRENT_VERSION()`
5. Store project overrides in `.claude/snowflake-config.json`

### Auth Methods
- Password (basic)
- Key-pair (recommended for automation)
- SSO/browser (interactive)

### Data Operations
- Load: `COPY INTO` from stage, direct query to DataFrame
- Unload: DataFrame to table, `COPY INTO` to stage
- Metadata: `INFORMATION_SCHEMA` queries

## Report Bus

Write report with: connection status, account info, available databases/schemas
```

- [ ] **Step 6: Commit**

```bash
git add agents/
git commit -m "feat: add 5 Snowflake agents with Extension Protocol frontmatter"
```

---

### Task 3: Create the 8 Skill Definitions

**Files:** Create 8 SKILL.md files under `skills/`.

- [ ] **Step 1: Create all 8 SKILL.md files**

Each follows the pattern: frontmatter + description + "Full Specification" link.

**snowflake-connect/SKILL.md:**
```yaml
---
name: snowflake-connect
description: "Setup and test Snowflake connection. Configures credentials, tests connectivity, stores project-specific overrides."
user_invocable: true
aliases: [sf connect, snowflake setup, snowflake auth]
extends: ml-automation
---
```

**snowflake-coldstart/SKILL.md:**
```yaml
---
name: snowflake-coldstart
description: "Full Snowflake ML workflow — connect, discover data, build pipeline, train model, deploy to Snowflake"
user_invocable: true
aliases: [sf coldstart, snowflake workflow, snowflake ml pipeline]
extends: ml-automation
---
```

**snowflake-sql/SKILL.md:**
```yaml
---
name: snowflake-sql
description: "Generate and execute Snowflake SQL from natural language — DDL, DML, queries with approval before execution"
user_invocable: true
aliases: [sf sql, snowflake query, snowflake ddl]
extends: ml-automation
---
```

**snowflake-pipeline/SKILL.md:**
```yaml
---
name: snowflake-pipeline
description: "Build Snowpark data transformation pipelines with DataFrame API"
user_invocable: true
aliases: [sf pipeline, snowpark pipeline, snowflake transform]
extends: ml-automation
---
```

**snowflake-train/SKILL.md:**
```yaml
---
name: snowflake-train
description: "Train models using Snowpark ML or Snowflake ML Functions (FORECAST, ANOMALY_DETECTION). Registers in Model Registry."
user_invocable: true
aliases: [sf train, snowpark ml train, snowflake model]
extends: ml-automation
---
```

**snowflake-deploy/SKILL.md:**
```yaml
---
name: snowflake-deploy
description: "Deploy to Snowflake — Model Registry, Streamlit in Snowflake, or stored procedure inference endpoint"
user_invocable: true
aliases: [sf deploy, snowflake model deploy, streamlit in snowflake]
extends: ml-automation
---
```

**snowflake-migrate/SKILL.md:**
```yaml
---
name: snowflake-migrate
description: "Migrate existing Python ML code (pandas, sklearn) to Snowpark equivalents"
user_invocable: true
aliases: [sf migrate, pandas to snowpark, snowpark migration]
extends: ml-automation
---
```

**snowflake-status/SKILL.md:**
```yaml
---
name: snowflake-status
description: "Check Snowflake resources — warehouse usage, deployed models, Streamlit apps, stored procedures, recent queries"
user_invocable: true
aliases: [sf status, snowflake resources, snowflake info]
extends: ml-automation
---
```

- [ ] **Step 2: Commit**

```bash
git add skills/
git commit -m "feat: add 8 Snowflake skill definitions with Extension Protocol frontmatter"
```

---

### Task 4: Create the 8 Command Files

**Files:** Create 8 command files under `commands/`.

All commands include Stage 0 (connection + utilities check). The implementer should write comprehensive command content following the patterns established in the MMM extension — each command is a detailed markdown workflow.

- [ ] **Step 1: Create snowflake-connect.md**

The connection setup command. Content:
- Check for `~/.snowflake/connections.toml`
- If exists: test with `SELECT CURRENT_VERSION()`, report status
- If not: interactive setup (account, user, role, warehouse, database, schema, auth)
- Write `connections.toml`
- Test connection
- Write `.claude/snowflake-config.json` for project overrides
- Report bus: `save_agent_report("snowflake-connector", {...})`

- [ ] **Step 2: Create snowflake-coldstart.md**

The full workflow command. Content:
- Stage 0: Ensure connection + utilities
- Stage 1: Connect & discover (schemas, tables, profile data)
- Stage 2: SQL development (DDL for staging/feature tables)
- Stage 3: Snowpark pipeline (transformation pipeline)
- Stage 4: Train (Snowpark ML or ML Functions)
- Stage 5: Evaluate (model evaluation, results to Snowflake)
- Stage 6: Deploy (Model Registry, Streamlit in Snowflake, stored procedures)
- Stage 7: Finalize (report, document resources)

- [ ] **Step 3: Create snowflake-sql.md**

Natural language to SQL command. Content:
- Stage 0: connection check
- Accept natural language description
- Generate Snowflake-optimized SQL
- Show SQL for user approval before execution
- Execute and display results
- Optionally save to `.sql` file

- [ ] **Step 4: Create snowflake-pipeline.md**

Snowpark pipeline builder. Content:
- Stage 0: connection check
- Read EDA report if available
- Generate Snowpark DataFrame transformation code
- Include data quality checks
- Save to `src/snowpark_pipeline.py`

- [ ] **Step 5: Create snowflake-train.md**

ML training on Snowflake. Content:
- Stage 0: connection check
- Two modes: Snowpark ML (sklearn-compatible) or ML Functions (FORECAST, ANOMALY_DETECTION)
- Train model
- Register in Snowflake Model Registry
- Log experiment via core's `log_experiment()`

- [ ] **Step 6: Create snowflake-deploy.md**

Deployment command. Content:
- Stage 0: connection check
- Three targets: Model Registry, Streamlit in Snowflake, Stored Procedure
- For each target: step-by-step deployment
- Verify deployment
- Report deployed resources

- [ ] **Step 7: Create snowflake-migrate.md**

Migration command. Content:
- Stage 0: connection check
- Scan project for pandas/sklearn code
- Generate Snowpark equivalents
- Show diff for approval
- Write migrated code

- [ ] **Step 8: Create snowflake-status.md**

Status command. Content:
- Stage 0: connection check
- Query INFORMATION_SCHEMA and ACCOUNT_USAGE
- Report: warehouses, models, Streamlit apps, stored procedures, recent queries
- Format as table

- [ ] **Step 9: Commit**

```bash
git add commands/
git commit -m "feat: add 8 Snowflake commands with Stage 0 connection checks"
```

---

### Task 5: Create snowflake_utils.py

**Files:**
- Create: `~/Documents/ml-automation-snowflake/templates/snowflake_utils.py`

- [ ] **Step 1: Write snowflake_utils.py**

Complete utility library with: connection management, query execution, data load/write, Snowpark session, relevance detection, metadata queries, model registry registration. See spec Section 5 for full function signatures.

- [ ] **Step 2: Commit**

```bash
git add templates/
git commit -m "feat: add snowflake_utils.py with connection, query, Snowpark, and model registry utilities"
```

---

### Task 6: Create hooks.json

**Files:**
- Create: `~/Documents/ml-automation-snowflake/hooks/hooks.json`

- [ ] **Step 1: Create empty hooks.json**

```json
{
  "hooks": {}
}
```

- [ ] **Step 2: Commit**

```bash
git add hooks/
git commit -m "feat: add empty hooks.json for future Snowflake-specific hooks"
```

---

### Task 7: Create README and Publish

**Files:**
- Create: `~/Documents/ml-automation-snowflake/README.md`

- [ ] **Step 1: Write README**

Include: prerequisites, installation, agents table (5 agents with hooks), commands table (8 commands), integration guide (how hooks fire in core workflows), connection setup guide.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with installation, commands, and integration guide"
```

- [ ] **Step 3: Create GitHub repo and push**

```bash
cd ~/Documents/ml-automation-snowflake
gh repo create Maxilylm/ml-automation-snowflake --public --description "Snowflake development and ML automation extension for ml-automation" --source . --push
```

---

### Task 8: Add to Marketplace and Push

**Files:**
- Modify: `/Users/maximolorenzoylosada/Documents/ml-automation-plugin/.claude-plugin/marketplace.json`

- [ ] **Step 1: Add Snowflake entry to marketplace**

Add new plugin entry for `ml-automation-snowflake`.

- [ ] **Step 2: Commit and push**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: add ml-automation-snowflake to marketplace"
git push origin HEAD:main
```
