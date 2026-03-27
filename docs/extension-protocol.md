# Extension Protocol Guide

## Overview

The ml-automation plugin supports extensions — separate Claude Code plugins that add domain-specific agents, skills, and commands while integrating with core workflows.

## Prerequisites

Extensions require the `ml-automation` core plugin to be installed. Your extension's `plugin.json` should declare this:

```json
{
  "dependencies": {
    "ml-automation": ">=1.8.0"
  }
}
```

## Extension Agent Frontmatter

Extension agents must include these fields in their YAML frontmatter:

| Field | Required | Purpose |
|---|---|---|
| `extends: ml-automation` | Yes | Declares this agent as part of the ml-automation ecosystem |
| `routing_keywords` | No | List of terms for the assigner to route tasks to this agent |
| `hooks_into` | No | List of core hook points where this agent should be spawned |

### Example

```yaml
---
name: mmm-analyst
description: Media Mix Modeling analysis and optimization
model: sonnet
extends: ml-automation
routing_keywords: [mmm, media mix, marketing mix, channel attribution, adstock]
hooks_into:
  - after-eda
  - after-evaluation
---
```

## Available Hook Points

| Hook Point | Fires After | Available In |
|---|---|---|
| `after-init` | Data validation complete | /team-coldstart |
| `after-eda` | EDA + reflection gate passed | /team-coldstart, /eda |
| `after-feature-engineering` | Feature engineering complete | /team-coldstart |
| `after-preprocessing` | Preprocessing pipeline built | /team-coldstart, /preprocess |
| `before-training` | Pre-training reflection | /team-coldstart, /train |
| `after-training` | Training + reflection gate passed | /team-coldstart, /train |
| `after-evaluation` | Evaluation complete | /team-coldstart, /evaluate |
| `after-dashboard` | Dashboard created | /team-coldstart |
| `before-deploy` | Pre-deployment gate | /team-coldstart, /deploy |
| `after-deploy` | Deployment complete | /team-coldstart, /deploy |

## Hook Point Timing

All `after-*` hook points fire AFTER any reflection gates for that stage have passed. Your extension agent receives the final, gate-approved output — never intermediate pre-gate data.

## Versioning Contract

Hook point names are a versioned contract. The core plugin will NOT rename or remove hook points without a major version bump (e.g., 1.x -> 2.0) and a deprecation notice in the changelog. You can depend on hook point names being stable within a major version.

## Extension Plugin Structure

```
ml-automation-{name}/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── {agent-name}.md       # Must include extends: ml-automation
├── skills/
│   └── {skill-name}/
│       └── SKILL.md           # May include extends: ml-automation
├── commands/
│   └── {command-name}.md      # Can spawn core agents directly
├── templates/
│   └── {name}_utils.py        # Domain-specific utilities
└── hooks/
    └── hooks.json             # Extension-specific hooks
```

## Using Core Utilities

Extension commands that run standalone (outside /team-coldstart) must ensure ml_utils.py exists:

```markdown
## Stage 0: Initialize
If ml_utils.py is not present in the project, copy it from the core plugin:
- Scan for: `.claude/plugins/*/templates/ml_utils.py` or `~/.claude/plugins/*/templates/ml_utils.py`
- Copy to project's `src/` directory
```

Extension utilities can import from ml_utils:

```python
from ml_utils import save_agent_report, load_agent_report, log_experiment
```

## Report Bus Integration

Extension agents must write reports using the standard convention:

```python
save_agent_report("your-agent-name", {
    "status": "completed",
    "findings": { ... },
    "enables": ["downstream-agent-1", "downstream-agent-2"]
})
```

Reports are discoverable by all agents (core and extension) via `load_agent_reports()`.

## Routing Priority

Extension agents are routed at Priority 2.5 — after core domain-specific rules (Priority 2) but before review tasks (Priority 3). Core agents always take precedence.

## Error Handling

Extension agent failures at hook points do NOT block core workflows. The core logs a warning and continues. Extension-specific workflows (your own commands) should handle errors as needed.
