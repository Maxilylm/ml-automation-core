# ml-automation-mmm Extension Plugin Design

**Date:** 2026-03-27
**Status:** Draft
**Target Repo:** `Maxilylm/ml-automation-mmm`

## Problem

The Bayesian MMM (Media Mix Modeling) agent system at `BLEND360/spark-bayesian-mmm-agent` is a standalone project. It needs to be converted into an extension plugin for the ml-automation core, following the Extension Protocol defined in v1.8.0.

## Goal

Create `ml-automation-mmm` as a self-contained Claude Code plugin that:
1. Follows the Extension Protocol (`extends: ml-automation`)
2. Hooks into core workflows at `after-eda` and `after-evaluation`
3. Provides its own MMM-specific commands and workflows
4. Ships with the full knowledge base, scripts, and templates
5. Reuses core agents (eda-analyst, developer, mlops-engineer) where appropriate

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Scope | Full self-contained plugin | Users install and everything works immediately |
| Hook points | mmm-methodologist→after-eda, mmm-validator→after-evaluation | Natural MMM review points in core workflows |
| mmm-communicator hooks | None | Client reporting is MMM-specific, not a core workflow step |
| Model tier | All agents use `sonnet` | Core uses generic tiers; pinned model IDs break on rotation |
| Knowledge base | Shipped inside plugin | Commands reference KB paths relative to plugin root |

## Section 1: Plugin Manifest

```json
{
  "name": "ml-automation-mmm",
  "version": "0.1.0",
  "description": "Media Mix Modeling extension for ml-automation. Bayesian MMM with adstock, saturation, channel attribution, and client-ready reporting.",
  "author": { "name": "Maximo Lorenzo y Losada" },
  "repository": "https://github.com/Maxilylm/ml-automation-mmm",
  "license": "MIT",
  "keywords": ["mmm", "media-mix", "bayesian", "marketing", "ml-automation-extension", "pymc", "channel-attribution"],
  "dependencies": {
    "ml-automation": ">=1.8.0"
  }
}
```

## Section 2: Agent Definitions

### mmm-methodologist

```yaml
---
name: mmm-methodologist
description: "Design and review Marketing Mix Models using the internal MMM knowledge pack. Selects modeling choices (adstock/saturation, hierarchy, priors), aligns validation strategy, and drafts MMM design memos."
model: sonnet
color: "#FF6B35"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [mmm, media mix, marketing mix, adstock, saturation, bayesian mmm, channel attribution, media optimization, marketing budget, roas]
hooks_into:
  - after-eda
---
```

Body: Existing mmm-methodologist content (retrieval rules, deliverables, next step suggestion). Add a relevance gate preamble:

```markdown
## Relevance Gate (when running at a hook point)

When invoked at a core workflow hook point (not via direct command):
1. Read `.claude/reports/eda-analyst_report.json`
2. Check if the dataset contains marketing/media spend columns (keywords: spend, cost, impressions, clicks, media, channel, campaign, ad, marketing)
3. If NO marketing columns detected: write `save_agent_report("mmm-methodologist", {"status": "skipped", "reason": "No marketing spend columns detected"})` and exit
4. If marketing columns detected: proceed with full methodology review
```

### mmm-validator

```yaml
---
name: mmm-validator
description: "Validate MMM implementation and results against the internal validation checklist. Focuses on diagnostics, plausibility, leakage, stability, and calibration alignment."
model: sonnet
color: "#E85D04"
tools: [Read, Write, Bash(*), Glob, Grep]
extends: ml-automation
routing_keywords: [mmm validation, mmm diagnostics, mmm plausibility, roas check, contribution check, mmm verify]
hooks_into:
  - after-evaluation
---
```

Body: Existing mmm-validator content. Add same relevance gate pattern (check for MMM model artifacts in `models/` or `reports/mmm/`).

### mmm-communicator

```yaml
---
name: mmm-communicator
description: "Convert MMM technical results into client-ready business narratives using internal delivery patterns (exec summary, key findings, recommendations, caveats)."
model: sonnet
color: "#DC2F02"
tools: [Read, Write, Glob, Grep]
extends: ml-automation
routing_keywords: [mmm report, mmm client report, mmm narrative, mmm delivery, mmm presentation]
---
```

Body: Existing mmm-communicator content unchanged. No `hooks_into` — only used in MMM-specific workflows.

## Section 3: Skills and Commands

Each source command maps 1:1 to a skill + command pair following core conventions.

| Skill | SKILL.md | Command | Source |
|---|---|---|---|
| `start-mmm-project` | `skills/start-mmm-project/SKILL.md` | `commands/start-mmm-project.md` | `/start-mmm-project` |
| `train-bmmm` | `skills/train-bmmm/SKILL.md` | `commands/train-bmmm.md` | `/train-bmmm` |
| `bmmm-smoke` | `skills/bmmm-smoke/SKILL.md` | `commands/bmmm-smoke.md` | `/bmmm-smoke` |
| `final-mmm-report` | `skills/final-mmm-report/SKILL.md` | `commands/final-mmm-report.md` | `/final-mmm-report` |
| `mmm-communicate` | `skills/mmm-communicate/SKILL.md` | `commands/mmm-communicate.md` | `/mmm-communicate` |
| `mmm-methodologist` | `skills/mmm-methodologist/SKILL.md` | `commands/mmm-methodologist.md` | Gate command |
| `ensure-bmmm-env` | `skills/ensure-bmmm-env/SKILL.md` | `commands/ensure-bmmm-env.md` | `/ensure-bmmm-env` |
| `self-assess` | `skills/self-assess/SKILL.md` | `commands/self-assess.md` | `/self-assess` |

### Skill Frontmatter Pattern

Each SKILL.md follows core conventions:

```yaml
---
name: start-mmm-project
description: "Bootstrap a new MMM project — generates problem brief, data readiness checklist, and design memo from the MMM knowledge pack"
user_invocable: true
aliases: [mmm start, start mmm, bootstrap mmm]
extends: ml-automation
---
```

### Command Content

Command files are the existing source content with these adjustments:
- Path references to `knowledge_base/mmm/` remain as-is (resolve relative to plugin root)
- Commands that produce reports use `save_agent_report()` from core `ml_utils`
- The `/start-mmm-project` command includes a Stage 0 that ensures `ml_utils.py` is present (per Extension Protocol)

## Section 4: Plugin Directory Structure

```
ml-automation-mmm/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── mmm-communicator.md
│   ├── mmm-methodologist.md
│   └── mmm-validator.md
├── skills/
│   ├── start-mmm-project/
│   │   └── SKILL.md
│   ├── train-bmmm/
│   │   └── SKILL.md
│   ├── bmmm-smoke/
│   │   └── SKILL.md
│   ├── final-mmm-report/
│   │   └── SKILL.md
│   ├── mmm-communicate/
│   │   └── SKILL.md
│   ├── mmm-methodologist/
│   │   └── SKILL.md
│   ├── ensure-bmmm-env/
│   │   └── SKILL.md
│   └── self-assess/
│       └── SKILL.md
├── commands/
│   ├── start-mmm-project.md
│   ├── train-bmmm.md
│   ├── bmmm-smoke.md
│   ├── final-mmm-report.md
│   ├── mmm-communicate.md
│   ├── mmm-methodologist.md
│   ├── ensure-bmmm-env.md
│   └── self-assess.md
├── knowledge_base/
│   └── mmm/                     # Full KB shipped with plugin
│       ├── 00_CORE.md
│       ├── 02_KB_INDEX.yml
│       ├── chunks/
│       ├── templates/
│       │   ├── problem_brief_mmm.md
│       │   ├── data_readiness_mmm.md
│       │   ├── design_memo_mmm.md
│       │   └── delivery_summary_mmm.md
│       ├── playbook/
│       ├── validation_checklist_mmm.yaml
│       └── BMMM-env/            # Environment config (environment.yaml, requirements.txt)
├── scripts/
│   ├── mmm/
│   │   └── build.py
│   ├── ensure_domain_env.py
│   ├── ensure_bmmm_env.py
│   └── run_in_env.py
├── templates/
│   └── mmm_utils.py
└── hooks/
    └── hooks.json
```

## Section 5: Report Bus Integration

MMM agents write reports to the standard report bus:

| Agent | Report File |
|---|---|
| mmm-methodologist | `.claude/reports/mmm-methodologist_report.json` |
| mmm-validator | `.claude/reports/mmm-validator_report.json` |
| mmm-communicator | `.claude/reports/mmm-communicator_report.json` |

Reports follow core schema (`status`, `findings`, `enables`) and are discoverable by `load_agent_reports()`.

MMM-specific artifacts (design memo, data readiness, final report) go to `reports/mmm/<project>/<run_id>/` — this is the MMM domain's own artifact structure, separate from the agent report bus.

## Section 6: mmm_utils.py

Thin utility layer for MMM-specific operations. Imports from core `ml_utils`:

```python
from ml_utils import save_agent_report, load_agent_report, log_experiment

def detect_mmm_relevance(df_or_report):
    """Check if dataset has marketing/media spend columns suggesting MMM."""
    mmm_keywords = {"spend", "cost", "impressions", "clicks", "media",
                    "channel", "campaign", "ad", "marketing", "adstock"}
    # Check column names against keywords
    ...

def compute_adstock(series, decay_rate=0.5):
    """Apply adstock transformation to media spend series."""
    ...

def decompose_contributions(model, X):
    """Decompose model predictions into channel contributions."""
    ...
```

## Section 7: What Gets Created (Scope)

### New Repository: `Maxilylm/ml-automation-mmm`

1. **Plugin manifest** — `.claude-plugin/plugin.json`
2. **3 agents** — with Extension Protocol frontmatter, relevance gates, existing body content
3. **8 skill definitions** — SKILL.md files with frontmatter
4. **8 commands** — existing command content with minor path/protocol adjustments
5. **Knowledge base** — copied from source repo
6. **Scripts** — copied from source repo
7. **mmm_utils.py** — new thin utility layer
8. **hooks.json** — empty or minimal (MMM-specific hooks if needed)
9. **README.md** — installation and usage guide

### Not In Scope

- Modifying the core plugin (already done in v1.8.0)
- Creating the knowledge base content (it exists in the source repo)
- Writing the MCMC training code (it exists in `scripts/mmm/build.py`)
