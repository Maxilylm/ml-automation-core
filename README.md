# ML Automation Plugin

End-to-end machine learning automation workflow for AI coding assistants. Takes you from raw data to deployed model with interactive dashboard — orchestrated by specialized AI agents.

Supports **Claude Code**, **Cursor**, **Codex**, and **OpenCode**.

## What's New in v1.5 (v1.5.0 — v1.5.3)

### Evaluation Framework

Built-in eval definitions for all 12 skills and agent routing, with a CLI runner for tracking quality across iterations:

```bash
# Initialize a new eval iteration
python evals/eval_runner.py --init-iteration 1

# Record results after running a skill against its eval prompt
python evals/eval_runner.py --record eda sales-data-exploration sales-correlation pass

# View pass/fail summary
python evals/eval_runner.py --summary

# Compare across iterations to catch regressions
python evals/eval_runner.py --compare 1 2
```

**30 evals** with **78 assertions** covering:
- All 12 skills (EDA, preprocess, train, evaluate, deploy, test, report, status, registry, team-coldstart, team-analyze, team-review)
- 15 routing accuracy tests for the assigner agent

Eval definitions are versioned in `evals/`. Iteration outputs are gitignored.

### Routing Overhaul (33% → 100% accuracy)

The assigner agent was restructured with a 6-level priority system. Domain-specific compound rules now fire **before** generic implementation keywords, eliminating all misroutes:

1. **Multi-agent coordination** → `orchestrator` (catches "coordinate the whole thing")
2. **Domain-specific rules** → MLOps, ML theory, feature engineering, data investigation (catches "set up monitoring", "add features from customer data")
3. **Review/analysis** → appropriate analyst
4. **Diagnostic language** → `developer` (catches "something's wrong", "broken")
5. **Implementation keywords** → `developer` (only if no higher-priority rule matched)
6. **Fallback** → `orchestrator`

Additional keyword coverage:
- **Diagnostic language**: "wrong", "broken", "not working", "crash" → developer
- **ML methodology**: leakage, overfitting, regularization → ml-theory-advisor
- **MLOps**: retraining, drift, monitoring, serving → mlops-engineer
- **Feature engineering**: feature importance, interaction terms + data context → feature-engineering-analyst
- **Contextual disambiguation table** for ambiguous terms (pipeline, features, model, accuracy)

### Skill Quality Overhaul

All 12 SKILL.md files expanded from ~20 lines to ~50 lines with:
- Report Bus integration (v1.2.0)
- Version feature awareness (v1.2-v1.4)
- Agent coordination details
- Flags and configuration options
- Pointer to full command specification

### EDA Improvements

- Date range validation (catches future dates, impossibly old dates)
- Categorical label consistency checks (case variants like "Active"/"ACTIVE", semantic aliases like "NY"/"New York")
- Near-duplicate detection guidance (subset-based, not just exact row match)
- Domain-invalid range detection (negative ages, negative prices)

### Preprocessing Improvements

- **Active leakage scan** (step 1b): Feature-target correlation >0.90 and feature-feature correlation >0.95 flagged before pipeline construction
- Pipeline artifact saving with `joblib.dump`
- Updated Data Leakage Prevention Checklist with correlation thresholds

### Agent Description Trimming

Agent YAML frontmatter descriptions reduced ~90% (1800-2640 chars → 121-265 chars). XML examples moved to markdown body. Reduces token usage during routing decisions.

### Bug Fixes

- Fix 6 phantom agent references (pr-reviewer, qa-test-agent, snowflake-engineer, data-steward, project-manager)
- Remove `/report` "status" alias that conflicted with `/status`
- Replace hardcoded OpenCode-only ml_utils paths with multi-platform discovery

### Orchestrator Update

Now aware of all 9 agents and all version features (v1.2.0 report bus, v1.2.1 reflection gates, v1.3.0 MLOps registry, v1.4.0 self-check loops and lessons learned).

## What's New in v1.4.0

### Iterative Self-Check Loops

Every workflow stage now validates its output before proceeding. If validation fails, the agent is re-spawned with error feedback (configurable max iterations). This generalizes the dashboard smoke test to ALL stages:

- **EDA**: Report completeness, required keys, non-empty statistics
- **Feature Engineering**: Features list populated, no duplicates, leakage assessed
- **Preprocessing**: Pipeline file exists, tests exist
- **Training**: Model artifact present, experiment logged
- **Evaluation**: Evaluation report complete
- **Dashboard**: Syntax, placeholders, imports (existing enhanced)

```bash
/team coldstart data.csv --max-check 3   # Allow 3 retry iterations
/team coldstart data.csv --max-check 0   # Skip self-checks
```

### Pre-Stage Reflection

Before each major stage, a domain expert agent plans the approach by reading all prior reports and lessons. The executing agent reads this plan before starting, leading to better first-attempt quality.

| Stage | Reflector |
|-------|-----------|
| Analysis | ml-theory-advisor |
| Processing | ml-theory-advisor |
| Modeling | ml-theory-advisor |
| Evaluation | ml-theory-advisor |
| Dashboard | frontend-ux-analyst |
| Production | mlops-engineer |

```bash
/team coldstart data.csv                    # With pre-reflection (default)
/team coldstart data.csv --no-pre-reflect   # Skip pre-stage reflection
```

### Lessons Learned System

Persistent knowledge base that records mistakes, solutions, and successful patterns. Lessons are:
- **Written** when self-checks fail, reflection gates request revision, or agents recover from errors
- **Consulted** before each stage in pre-reflection prompts and agent spawn prompts
- **Deduplicated** automatically (same stage + similar title → increment counter)
- **Persisted** across workflow runs in `.claude/lessons-learned.json`

```bash
/status --lessons   # View all recorded lessons
```

### New Utility Functions

Added to `ml_utils.py`:
- `save_lesson()`, `load_lessons()`, `get_relevant_lessons()`, `format_lessons_for_prompt()`
- `validate_stage_output()` with per-stage validators
- `save_stage_plan()`, `load_stage_plan()`

## What's New in v1.2.0

### Shared Report Bus
All 10 agents now communicate through a shared JSON report system. Each agent reads prior reports on startup and writes its own report on completion, enabling:
- Cross-agent insights and recommendations
- Convention-based discovery (`*_report.json` files)
- Multi-platform support (`.claude/reports/`, `.cursor/reports/`, etc.)

### Parallel Agent Execution
Workflow commands now spawn agents in parallel where dependencies allow:
- **Post-EDA group**: feature-engineering-analyst + ml-theory-advisor + frontend-ux-analyst run concurrently
- **Post-Training review group**: brutal-code-reviewer + ml-theory-advisor + frontend-ux-analyst run concurrently

### `/status` Command
New slash command for unified workflow visibility:
```bash
/status              # Show full workflow status
/status --agent eda  # Show specific agent's report
/status --pending    # Show only pending work
```

### Report Validation Hooks
Automatic schema validation after each agent completes, ensuring reports are well-formed and discoverable.

## What's New in v1.2.1

### Reflection Gates

Pre-execution validation gates that evaluate the *strategy* before the next workflow stage proceeds:

- **Gate 1** (post-feature-engineering): Validates feature strategy, domain-specific transformations, leakage risk
- **Gate 2** (post-preprocessing): Validates pipeline design, encoding choices, data flow
- **Gate 3** (post-training): Validates model family, hyperparameter strategy, validation approach

If issues are found, the upstream agent re-runs with corrections (max 2 iterations by default, configurable with `--max-reflect`).

```bash
# Use reflection gates (default)
/team coldstart data.csv --target Revenue

# Skip reflection gates
/team coldstart data.csv --target Revenue --max-reflect 0

# Allow more iterations
/team coldstart data.csv --target Revenue --max-reflect 3
```

## What's New in v1.3.0

### MLOps Registry Layer

Convention-based MLOps registries — no external dependencies required:

- **Model Registry**: Track trained models with metrics, lineage, rationale, and champion/challenger status
- **Feature Store**: Catalog engineered features with transformations, statistics, and reusability metadata
- **Experiment Tracking**: Log every training run with hyperparameters, metrics, and approach rationale
- **Data Versioning**: Fingerprint datasets for reproducibility

Task-type aware — adapts metrics and validation for classification, regression, MMM, segmentation, and time series.

```bash
# Inspect registries
/registry                          # Summary of all registries
/registry models --champion        # Show champion model details
/registry features --domain mmm    # Filter features by domain
/registry lineage model_id         # Trace full lineage
```

## What's New in v1.3.1

### Report Verification Checkpoints

Orchestrator-level enforcement that every agent saves its report after parallel stages:

- **Step 2b-verify**: Checks ml-theory-advisor, feature-engineering-analyst, frontend-ux-analyst reports after post-EDA analysis
- **Step 5b-verify**: Checks brutal-code-reviewer, ml-theory-advisor, frontend-ux-analyst reports after post-training review
- **Step 5c-verify**: Checks mlops-engineer report after registry validation
- **team-analyze Step 4b**: Checks ml-theory-advisor and feature-engineering-analyst reports

If any report is missing, the agent is re-spawned once with explicit save instructions. If still missing after retry, a warning is logged and the workflow proceeds.

### Grounded Dashboard Creation

Stage 6 no longer uses a placeholder template (`"{count}"`, `"{value}"`, `fig_overview`). Instead:

- Developer agent must read actual report files before writing code
- All variables must be defined before use — no undefined names
- Data is loaded and computed at runtime, not hardcoded

### Dashboard Smoke Test Loop

After dashboard creation, a validation loop (max 2 iterations) checks for:

1. **Syntax errors** via `ast.parse`
2. **Unresolved placeholders** via regex (`"{...}"` patterns)
3. **Undefined variables** via import-level execution with mocked Streamlit

If validation fails, the developer is re-spawned to fix issues. After max retries, a minimal fallback dashboard is written.

### Upgraded Post-Dashboard Hook

The `post-dashboard.sh` hook now validates beyond basic `py_compile`:

- `ast.parse` for syntax checking
- Placeholder regex detection (exits 1 on `"{...}"` patterns)
- Import-level check with mocked Streamlit (catches `NameError`/`ImportError`, tolerates runtime errors)

## What's Included

### 10 Specialized Agents

| Agent | Role |
|-------|------|
| `eda-analyst` | Exploratory data analysis on any dataset |
| `ml-theory-advisor` | ML theory guidance, data leakage prevention |
| `feature-engineering-analyst` | Feature design and opportunity discovery |
| `mlops-engineer` | Model deployment, APIs, Docker, CI/CD |
| `developer` | Code implementation on feature branches |
| `brutal-code-reviewer` | Code quality and maintainability review |
| `pr-approver` | Pull request review and merge |
| `frontend-ux-analyst` | UI/UX design feedback |
| `orchestrator` | Multi-agent coordination |
| `assigner` | Automatic ticket routing |

### Skills / Slash Commands

| Skill | Description |
|-------|-------------|
| `eda` | Run exploratory data analysis |
| `preprocess` | Build data processing pipeline (leakage-safe) |
| `train` | Train ML models with proper validation |
| `evaluate` | Comprehensive model evaluation with visualizations |
| `deploy` | Deploy to Docker, Snowflake, AWS, or GCP |
| `report` | Generate EDA, model, drift, or project reports |
| `test` | Generate and run tests (80% coverage threshold) |
| `team-coldstart` | Full pipeline: raw data to deployed dashboard |
| `team-analyze` | Quick multi-agent data analysis |
| `team-review` | Multi-agent code review |
| `status` | Show workflow status and agent reports |
| `registry` | Inspect MLOps registries (models, features, experiments, data) |

### Hooks

- **Pre-commit**: Python syntax check, secrets detection, test coverage validation
- **Pre-deploy**: Deployment readiness checks (files, health endpoints, Docker, env vars)
- **Post-EDA**: Extract metrics, flag data quality issues
- **Post-dashboard**: Validate syntax (`ast.parse`), detect placeholders, import-level check, generate run scripts
- **Post-workflow**: Summarize outputs, generate quick-start commands

## Installation

### Claude Code

**Option 1: Install from marketplace (recommended)**

1. Open Claude Code and run `/plugin`
2. Select **"Add marketplace"**
3. Enter: `maxilylm/ml-automation-plugin`
4. Select **"Install plugins"** and choose `ml-automation`
5. Restart Claude Code

**Option 2: Local development**

```bash
git clone https://github.com/maxilylm/ml-automation-plugin.git
claude --plugin-dir /path/to/ml-automation-plugin
```

### Cursor

```bash
git clone https://github.com/maxilylm/ml-automation-plugin.git
```

Place the repo (or symlink it) where Cursor discovers plugins. The `.cursor-plugin/plugin.json` manifest handles discovery automatically.

### Codex

1. **Clone the repository:**
   ```bash
   git clone https://github.com/maxilylm/ml-automation-plugin.git ~/.codex/ml-automation
   ```

2. **Create the skills symlink:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/ml-automation/commands ~/.agents/skills/ml-automation
   ```

   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\ml-automation" "$env:USERPROFILE\.codex\ml-automation\commands"
   ```

3. **Restart Codex** to discover the skills.

### OpenCode

1. **Clone the repository:**
   ```bash
   git clone https://github.com/maxilylm/ml-automation-plugin.git ~/.config/opencode/ml-automation
   ```

2. **Register the plugin:**
   ```bash
   mkdir -p ~/.config/opencode/plugins
   ln -s ~/.config/opencode/ml-automation/.opencode/plugins/ml-automation.js ~/.config/opencode/plugins/ml-automation.js
   ```

3. **Symlink skills:**
   ```bash
   mkdir -p ~/.config/opencode/skills
   ln -s ~/.config/opencode/ml-automation/commands ~/.config/opencode/skills/ml-automation
   ```

4. **Restart OpenCode.** Verify by asking: "what ML automation skills do you have?"

## Quick Start

```bash
# Full pipeline from raw data to deployed dashboard
/team-coldstart data/sales.csv --target Revenue

# Just explore a dataset
/eda data/customers.csv

# Quick multi-agent analysis
/team-analyze data/survey.csv

# Train a model
/train

# Deploy to Docker
/deploy local
```

## How It Works

The plugin provides a complete ML workflow where agents collaborate:

```
Raw Data → /eda → /preprocess → /train → /evaluate → /deploy
              ↓         ↓           ↓          ↓
         eda-analyst  ml-theory  ml-theory  mlops-engineer
                      advisor    advisor
```

Or run the full pipeline with a single command:

```
/team-coldstart data.csv --target y
```

This orchestrates all stages automatically:
1. Validates data and detects task type (ML vs analysis)
2. Runs parallel EDA, leakage review, and feature analysis
3. Builds preprocessing pipeline with leakage prevention
4. Trains and compares models
5. Generates comprehensive evaluation
6. Creates interactive Streamlit dashboard
7. Packages for production (FastAPI + Docker)
8. Deploys to target environment

## Updating

| Platform | Command |
|----------|---------|
| Claude Code | Run `/plugin` → Update marketplace |
| Codex | `cd ~/.codex/ml-automation && git pull` |
| OpenCode | `cd ~/.config/opencode/ml-automation && git pull` |
| Cursor | `cd <plugin-path> && git pull` |

Skills update instantly through symlinks — no reinstall needed.

## Requirements

- Python 3.9+
- Common ML libraries: pandas, scikit-learn, matplotlib, seaborn
- Optional: streamlit, fastapi, docker

## License

MIT
