# Modular Extension Architecture Design

**Date:** 2026-03-27
**Status:** Implemented
**Branch:** `feature/modular-extension-architecture`

## Problem

The ml-automation plugin is a monolithic system where all agents, skills, commands, and routing rules are hardcoded within a single plugin. Adding new domain-specific capabilities (e.g., Media Mix Modeling, Snowflake integration) requires modifying the core — increasing bloat, coupling, and maintenance burden.

## Goal

Make the core plugin extensible so that **separate plugins** can add agents, skills, and commands that integrate seamlessly with core workflows — without modifying the core itself.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Distribution model | Separate repos, separate Claude Code plugins | Independent versioning, install only what you need |
| Extension workflows | Extensions bring own commands AND hook into core workflows | Maximum flexibility for extension authors |
| Discovery mechanism | Self-describing agents via frontmatter metadata | Single source of truth, no new file formats, follows convention-over-configuration |
| Shared utilities | Core owns ml_utils, extensions depend on it | Simplest approach, natural prerequisite relationship |
| Workflow injection | Named hook points at stage boundaries | Explicit, predictable, debuggable |

## Section 1: Extension Protocol — Frontmatter Conventions

The extension protocol is a set of frontmatter fields that extension plugins use to declare their relationship to the core.

### Agent Frontmatter (extension agents)

Extension agents add three new optional fields:

```yaml
---
name: mmm-analyst
description: Media Mix Modeling analysis and optimization
model: sonnet
color: "#FF6B35"
tools: [Read, Write, Bash(*), Glob, Grep]
# --- Extension Protocol fields ---
extends: ml-automation
routing_keywords: [mmm, media mix, marketing mix, channel attribution, adstock]
hooks_into:
  - after-eda
  - after-evaluation
---
```

**Fields:**

- `extends: ml-automation` — required for the core to recognize an extension agent
- `routing_keywords` — list of terms the assigner uses to route tasks to this agent
- `hooks_into` — list of core hook point names where this agent should be spawned

### Skill Frontmatter (extension skills)

```yaml
---
name: mmm-coldstart
description: End-to-end Media Mix Modeling workflow
user_invocable: true
aliases: [mmm, media-mix]
extends: ml-automation
---
```

**Fields:**

- `extends: ml-automation` — same protocol field as agents

### Rules

- `extends: ml-automation` is required for the core to recognize an extension component
- `routing_keywords` feeds the assigner's dynamic routing
- `hooks_into` must reference valid hook point names defined by the core (see Section 2)
- Core agents do not need any frontmatter changes

## Section 2: Core Hook Points

Named stage boundaries in core workflows where extension agents can inject execution. This list is a versioned contract.

### Hook Points for `/team-coldstart`

| Hook Point | Fires After | Before | Purpose |
|---|---|---|---|
| `after-init` | Stage 1: Initialize | Stage 2: Analysis | Post-setup, data validated |
| `after-eda` | Stage 2: EDA + Analysis (after reflection gate 1) | Stage 3: Processing | Data understood, reflection gate passed, pre-processing |
| `after-feature-engineering` | Feature engineering complete (after reflection gate if applicable) | Preprocessing | Features designed, before pipeline |
| `after-preprocessing` | Stage 3: Processing | Stage 4: Modeling | Clean data ready |
| `before-training` | Pre-stage reflection | Training execution | Last chance to influence model strategy |
| `after-training` | Stage 4: Modeling | Stage 5: Evaluation | Model trained, pre-evaluation |
| `after-evaluation` | Stage 5: Evaluation | Stage 6: Dashboard | Metrics available |
| `after-dashboard` | Stage 6: Dashboard | Stage 7: Productionalize | Visuals ready |
| `before-deploy` | Stage 7: Productionalize | Stage 8: Deploy | Pre-deployment gate |
| `after-deploy` | Stage 8: Deploy | Stage 9: Finalize | Post-deployment |

### Hook Points for Other Core Commands

| Command | Hook Points |
|---|---|
| `/eda` | `after-eda` |
| `/train` | `before-training`, `after-training` |
| `/evaluate` | `after-evaluation` |
| `/deploy` | `before-deploy`, `after-deploy` |
| `/preprocess` | `after-preprocessing` |

### Hook Point Timing Rule

All `after-*` hook points fire **after** any reflection gates associated with that stage have passed. Extension agents receive the final, gate-approved output — never intermediate pre-gate data.

### Hook Execution Contract

When the core reaches a hook point:

1. **Discover** — scan all installed plugin agent files for `hooks_into` containing this hook point
2. **Collect** — gather all matching extension agents
3. **Spawn sequentially** — run each extension agent, passing it the current report bus state (all prior `*_report.json` files). If multiple independent extensions hook into the same point, they may be spawned in parallel (same pattern as core parallel execution groups).
4. **Extension agent writes its report** — using `save_agent_report()` convention, making its output available to downstream stages
5. **On failure** — if an extension agent fails or produces no report, log a warning and continue the core workflow. Extension failures must not block core execution. The orchestrator should note the failure in its report for visibility.
6. **Continue** — core proceeds to the next stage

### Versioning

Hook points are versioned with the core plugin version. Renaming or removing a hook point is a major version bump with a deprecation notice. Extensions declare `extends: ml-automation` without a version constraint — hook point names are the implicit API.

## Section 3: Dynamic Discovery in Orchestrator and Assigner

### Discovery Mechanism

1. Scan plugin directories for all `agents/*.md` files. Claude Code loads plugins from:
   - Project-local: `.claude/plugins/*/agents/*.md`
   - User-global: `~/.claude/plugins/*/agents/*.md`
   - The orchestrator/assigner use `Glob` with these paths to find all agent files.
2. Parse YAML frontmatter — extract `name`, `extends`, `routing_keywords`, `hooks_into`
3. Filter — only include agents where `extends: ml-automation` is present
4. **Validate hook points** — if an agent declares a `hooks_into` value that doesn't match any known hook point, log a warning (likely a typo). Known hook points are listed in the orchestrator's prompt.
5. Build runtime agent table — core agents + validated extension agents

This logic lives in the orchestrator and assigner agent prompts as instructions. These agents already use `Glob` and `Read` tools — they scan at workflow start.

### Assigner Changes

Current assigner has 6 priority tiers (Priority 1: orchestrator for multi-agent tasks, Priority 2: domain-specific compound rules with sub-sections for MLOps/Data/ML-theory/Features, Priority 3: review tasks, Priority 4: diagnostic, Priority 5: implementation, Priority 6: fallback). New behavior:

1. Read all `agents/*.md` from all installed plugins (using discovery paths above)
2. Build routing table:
   - Core agents: use existing priority rules (unchanged)
   - Extension agents: match `routing_keywords` against ticket text
3. Priority ordering:
   - Core priority tiers 1-6 remain unchanged
   - Extension agents slot into a new **tier 2.5** (after domain-specific compound rules in Priority 2, before review tasks in Priority 3)
   - If multiple extension agents match, prefer the one with the highest ratio of matched keywords to total keywords (specificity), not raw count
4. Fallback remains: orchestrator

Extension agents never override core routing. They fill gaps for domain-specific requests that no core agent handles.

### Orchestrator Changes

1. At workflow start, scan for all agents with `extends: ml-automation`
2. Merge into available agents table alongside core agents
3. When reaching a hook point in any workflow:
   a. Find agents with `hooks_into` containing this hook point
   b. Spawn each one, passing current report bus context
   c. Wait for completion, collect reports
   d. Continue to next stage
4. For direct dispatch (non-workflow): use the merged agent table

### What Stays Hardcoded

- Core agent names and their roles
- Priority tier ordering in the assigner (core agents always take precedence)
- Stage ordering within core workflows (extensions inject between stages, never reorder)
- Reflection gate assignments (ml-theory-advisor) — extensions can add gates but not replace core ones

## Section 4: Extension Plugin Structure

### Directory Structure Example (`ml-automation-mmm`)

```
ml-automation-mmm/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── mmm-analyst.md           # extends: ml-automation
│   └── mmm-optimizer.md         # extends: ml-automation
├── skills/
│   ├── mmm-coldstart/
│   │   └── SKILL.md             # extends: ml-automation
│   └── mmm-evaluate/
│       └── SKILL.md
├── commands/
│   ├── mmm-coldstart.md
│   └── mmm-evaluate.md
├── templates/
│   └── mmm_utils.py             # imports from ml_utils
└── hooks/
    └── hooks.json
```

### Extension `plugin.json`

```json
{
  "name": "ml-automation-mmm",
  "version": "0.1.0",
  "description": "Media Mix Modeling extension for ml-automation",
  "author": { "name": "Maximo Lorenzo y Losada" },
  "keywords": ["mmm", "media-mix", "marketing", "ml-automation-extension"],
  "dependencies": {
    "ml-automation": ">=1.8.0"
  }
}
```

The `dependencies` field is documentation-only (Claude Code doesn't enforce plugin dependencies) but signals to users and future tooling that the core is required.

### Extension Commands Using Core Agents

Extension commands spawn core agents directly since all plugins are loaded into the same session:

```markdown
## Stage 1: Data Exploration
Spawn **eda-analyst** (core) to profile the marketing dataset.

## Stage 2: MMM Analysis
Spawn **mmm-analyst** (extension) to run media mix decomposition.

## Stage 3: Model Training
Spawn **developer** (core) to implement the MMM model using mmm_utils.py.
```

### Extension Utils Pattern

`templates/mmm_utils.py` adds domain-specific functions and imports core utilities:

```python
from ml_utils import save_agent_report, load_agent_report, log_experiment

def compute_adstock(series, decay_rate=0.5):
    """Apply adstock transformation to media spend series."""
    ...

def decompose_contributions(model, X):
    """Decompose model predictions into channel contributions."""
    ...
```

This works because the core's `ml_utils.py` is already copied into the user's project before any extension runs.

**Important:** Extension commands that run standalone (outside a core workflow like `/team-coldstart`) must ensure `ml_utils.py` exists in the project. Extension commands should include a Stage 0 step: "If `ml_utils.py` is not present in the project, copy it from the core plugin's `templates/` directory." The core's `ml_utils.py` path can be discovered by scanning plugin directories for `templates/ml_utils.py`.

## Section 5: Scope of Core Changes (This PR)

### Files to Modify

1. **`agents/orchestrator.md`** — Replace static agent table with dynamic discovery instructions. Add hook point execution logic.
2. **`agents/assigner.md`** — Add dynamic routing for extension agents via `routing_keywords`. Add priority tier 2.5.
3. **`commands/team-coldstart.md`** — Insert hook point markers at all 10 stage boundaries with discovery and spawn instructions.
4. **`commands/eda.md`**, **`train.md`**, **`evaluate.md`**, **`deploy.md`**, **`preprocess.md`** — Add relevant hook points.
5. **`templates/ml_utils.py`** — No discovery functions added here (ml_utils is copied into user projects and should not contain plugin-internal scanning logic). Only change: ensure `save_agent_report()` and `load_agent_report()` work correctly with extension agent IDs (no hardcoded agent name lists).

### Files to Create

6. **`docs/extension-protocol.md`** — Extension author guide covering frontmatter conventions, hook point reference, plugin structure, and utilities usage.

### Files NOT Changed

- Existing agent definitions (other than orchestrator/assigner)
- Existing skill definitions
- `plugin.json` — version bump only
- Hooks — unchanged
- Evals — new evals for extension discovery added separately
