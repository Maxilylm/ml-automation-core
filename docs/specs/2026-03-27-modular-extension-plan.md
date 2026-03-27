# Modular Extension Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the ml-automation plugin extensible so that separate plugins can register agents, skills, and hook into core workflows via a frontmatter-based Extension Protocol.

**Architecture:** Self-describing extension agents declare `extends: ml-automation`, `routing_keywords`, and `hooks_into` in their frontmatter. The core's orchestrator and assigner dynamically discover these agents at workflow start by scanning plugin directories. Core commands define named hook points at stage boundaries where extension agents are spawned automatically.

**Tech Stack:** Markdown (agent/command definitions), Python (ml_utils.py), JSON (evals)

**Spec:** `docs/specs/2026-03-27-modular-extension-architecture-design.md`

---

### Task 1: Make `get_workflow_status()` in ml_utils.py Dynamic

The `workflow_agents` list at line 436-440 of `templates/ml_utils.py` is hardcoded with 10 agent names. This must become dynamic so extension agents appear in workflow status.

**Files:**
- Modify: `templates/ml_utils.py:427-460` (get_workflow_status function)

- [ ] **Step 1: Read the current function**

Read `templates/ml_utils.py` lines 427-460 to confirm the exact code.

- [ ] **Step 2: Replace hardcoded agent list with dynamic discovery**

Replace the hardcoded `workflow_agents` list with logic that discovers agents from report files:

```python
def get_workflow_status():
    """Get status of all agents in the workflow — discovers agents dynamically from reports."""
    reports = load_agent_reports()

    # Build agent list dynamically from existing reports + known core agents
    core_agents = [
        "eda-analyst", "feature-engineering-analyst", "ml-theory-advisor",
        "frontend-ux-analyst", "developer", "brutal-code-reviewer",
        "pr-approver", "mlops-engineer", "orchestrator", "assigner",
    ]
    # Include any agent that has written a report (catches extension agents)
    discovered_agents = set(core_agents) | set(reports.keys())
    workflow_agents = sorted(discovered_agents)
```

Keep the rest of the function logic unchanged — it iterates `workflow_agents` and checks for reports.

- [ ] **Step 3: Verify no other hardcoded agent lists exist in ml_utils.py**

Search `templates/ml_utils.py` for any other hardcoded agent name lists or string literals that would break with extension agents. Fix any found.

- [ ] **Step 4: Commit**

```bash
git add templates/ml_utils.py
git commit -m "feat: make get_workflow_status() discover agents dynamically from reports"
```

---

### Task 2: Add Extension Discovery Instructions to Orchestrator

The orchestrator at `agents/orchestrator.md` has a static "Available Agents" table (lines 21-33). Add dynamic discovery logic and hook point execution instructions.

**Files:**
- Modify: `agents/orchestrator.md:21-33` (Available Agents table), lines ~117-129 (parallel groups), lines ~148-158 (reflection gates)

- [ ] **Step 1: Read the full orchestrator file**

Read `agents/orchestrator.md` to confirm exact content and line numbers.

- [ ] **Step 2: Add Extension Discovery section after the core agent table**

Keep the existing core agent table (lines 21-33) as-is. Add a new section immediately after it:

```markdown
### Extension Agent Discovery

At workflow start, discover extension agents from all installed plugins:

1. Use Glob to scan for agent files:
   - `.claude/plugins/*/agents/*.md`
   - `~/.claude/plugins/*/agents/*.md`
2. Read each agent file's YAML frontmatter
3. Include agents where `extends: ml-automation` is present
4. Extract `routing_keywords` and `hooks_into` fields
5. If a `hooks_into` value does not match a known hook point, log a warning:
   "WARNING: Agent {name} declares unknown hook point '{value}' — skipping that hook"
6. Merge discovered extension agents into the Available Agents table for this session

Known hook points: `after-init`, `after-eda`, `after-feature-engineering`, `after-preprocessing`, `before-training`, `after-training`, `after-evaluation`, `after-dashboard`, `before-deploy`, `after-deploy`
```

- [ ] **Step 3: Add Hook Point Execution section**

Add a new section after the Extension Discovery section:

```markdown
### Hook Point Execution

When a workflow reaches a named hook point:

1. Check discovered extension agents for `hooks_into` containing this hook point
2. **Timing rule:** All `after-*` hook points fire AFTER any reflection gates for that stage have passed. Extension agents receive gate-approved output only — never intermediate pre-gate data.
3. For each matching extension agent, spawn it with this context:
   "You are running at hook point '{hook_point}' in the core ml-automation workflow.
    Read all prior agent reports in .claude/reports/ for context.
    WHEN DONE: Write your report using save_agent_report('{agent_name}', {...})"
   If multiple independent extensions hook into the same point, they MAY be spawned in parallel (same pattern as core parallel execution groups).
4. If an extension agent fails or produces no report, log a warning and continue:
   "WARNING: Extension agent {name} failed at hook point {hook_point} — continuing workflow"
5. Extension agent failures must NOT block the core workflow
6. Record any extension failures in the orchestrator's own report under an `extension_failures` key for visibility
7. After all hook point agents complete (or fail), proceed to the next stage
```

- [ ] **Step 4: Commit**

```bash
git add agents/orchestrator.md
git commit -m "feat: add extension agent discovery and hook point execution to orchestrator"
```

---

### Task 3: Add Dynamic Routing to Assigner

The assigner at `agents/assigner.md` has static routing rules (lines 53-101). Add a new priority tier 2.5 for extension agents discovered via `routing_keywords`.

**Files:**
- Modify: `agents/assigner.md:23-33` (Available Agents table), lines ~53-101 (priority tiers)

- [ ] **Step 1: Read the full assigner file**

Read `agents/assigner.md` to confirm exact content and line numbers.

- [ ] **Step 2: Add Extension Discovery section after the core agent table**

Keep the existing core agent table (lines 23-33). Add a new section after it:

```markdown
### Extension Agent Discovery

At the start of routing, discover extension agents:

1. Use Glob to scan: `.claude/plugins/*/agents/*.md` and `~/.claude/plugins/*/agents/*.md`
2. Read YAML frontmatter of each agent file
3. Include agents where `extends: ml-automation` is present
4. Extract `routing_keywords` for each extension agent
5. These agents are available for routing in addition to the core agents above
```

- [ ] **Step 3: Add Priority 2.5 tier between existing Priority 2 and Priority 3**

Insert a new section between the existing Priority 2 (domain-specific compound rules) and Priority 3 (review/analysis tasks):

```markdown
### Priority 2.5: Extension Agent Routing

For each discovered extension agent, check if its `routing_keywords` match the ticket text:
- Compare each keyword against the ticket description (case-insensitive)
- If one or more keywords match, this agent is a candidate
- If multiple extension agents match, prefer the one with the highest specificity ratio:
  `matched_keywords / total_keywords` (a specialist with 3/4 matching beats a generalist with 3/10)
- Extension agents NEVER override core agent routing — they only match when no core agent (Priority 1-2) has already matched
```

- [ ] **Step 4: Commit**

```bash
git add agents/assigner.md
git commit -m "feat: add extension agent discovery and priority 2.5 routing tier to assigner"
```

---

### Task 4: Add Hook Points to `/team-coldstart`

Insert hook point markers at all 10 stage boundaries in `commands/team-coldstart.md`. Each hook point triggers extension agent discovery and spawning.

**Files:**
- Modify: `commands/team-coldstart.md` (10 insertion points across the file)

- [ ] **Step 1: Read team-coldstart.md to identify exact insertion points**

The 10 hook points and their insertion locations (after the stage output/before the next stage header):

| Hook Point | Insert After | Insert Before |
|---|---|---|
| `after-init` | Stage 1 output block (~line 182) | Stage 2 header (line 184) |
| `after-eda` | Gate 1 completion (~line 350) | Stage 3 header (line 352) |
| `after-feature-engineering` | Step 2b-check completion (~line 290) | Stage 2c Gate 1 (line 309) |
| `after-preprocessing` | Gate 2 completion (~line 418) | Stage 4 header (line 420) |
| `before-training` | Stage 4 Pre-Reflection (~line 424) | Stage 4 actions (line 426) |
| `after-training` | Gate 3 completion (~line 494) | Stage 5 header (line 497) |
| `after-evaluation` | Stage 5c completion (~line 627) | Stage 6 header (line 629) |
| `after-dashboard` | Stage 6 output (~line 800) | Stage 7 header (line 802) |
| `before-deploy` | Stage 7 output (~line 834) | Stage 8 header (line 836) |
| `after-deploy` | Stage 8 output (~line 857) | Stage 9 header (line 859) |

- [ ] **Step 2: Create the reusable hook point template**

Add this template near the top of team-coldstart.md, after the Stage Flow Pattern section (~line 61):

```markdown
### Extension Hook Point Template

At each named hook point in the workflow:

**Timing rule:** All `after-*` hook points fire AFTER reflection gates for that stage have passed. Extension agents receive gate-approved output only.

1. Scan for extension agents: use Glob to find agents in `.claude/plugins/*/agents/*.md` and `~/.claude/plugins/*/agents/*.md`
2. Read each agent's frontmatter — select those with `extends: ml-automation` and `hooks_into` containing the current hook point name
3. For each matching agent, spawn it with (multiple independent extensions may run in parallel):
   "You are running at hook point '{hook_point}' in the /team-coldstart workflow.
    Read all prior agent reports in .claude/reports/ for context on the workflow state.
    WHEN DONE: Write your report using save_agent_report('{your_agent_name}', {...})"
4. If an extension agent fails or produces no report, log a warning and continue
5. Proceed to the next stage after all hook point agents complete
```

- [ ] **Step 3: Insert the 10 hook point markers**

At each insertion point, add a block like:

```markdown
#### Hook Point: after-eda

Run the Extension Hook Point Template (above) with hook_point = "after-eda".
```

Insert all 10 hook points at their identified locations. Each is just 3 lines referencing the template.

- [ ] **Step 4: Verify no stage ordering is disrupted**

Read the modified file and confirm that hook points sit between stages without changing the execution order of core stages.

- [ ] **Step 5: Commit**

```bash
git add commands/team-coldstart.md
git commit -m "feat: add 10 extension hook points to team-coldstart workflow"
```

---

### Task 5: Add Hook Points to Individual Commands

Add relevant hook points to `/eda`, `/train`, `/evaluate`, `/deploy`, and `/preprocess` commands.

**Files:**
- Modify: `commands/eda.md` (add `after-eda`)
- Modify: `commands/train.md` (add `before-training`, `after-training`)
- Modify: `commands/evaluate.md` (add `after-evaluation`)
- Modify: `commands/deploy.md` (add `before-deploy`, `after-deploy`)
- Modify: `commands/preprocess.md` (add `after-preprocessing`)

- [ ] **Step 1: Read all 5 command files**

Read each file to confirm the exact location where hook points should be inserted (typically at the end, before the output/agent invocation section).

- [ ] **Step 2: Add hook point to eda.md**

Insert before the output section (before ~line 112):

```markdown
### Extension Hook Point: after-eda

Scan for extension agents with `hooks_into` containing "after-eda":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "after-eda"
3. Spawn each matching agent with current EDA report context
4. On failure: log warning, continue
```

- [ ] **Step 3: Add hook points to train.md**

Insert two hook points — `before-training` before the training steps begin (~line 37), and `after-training` before the output section (~line 88).

- [ ] **Step 4: Add hook point to evaluate.md**

Insert `after-evaluation` before the output section (~line 64).

- [ ] **Step 5: Add hook points to deploy.md**

Insert `before-deploy` before the deployment targets section (~line 12) and `after-deploy` before the agent invocation section (~line 305).

- [ ] **Step 6: Add hook point to preprocess.md**

Insert `after-preprocessing` before the output section (~line 172).

- [ ] **Step 7: Commit**

```bash
git add commands/eda.md commands/train.md commands/evaluate.md commands/deploy.md commands/preprocess.md
git commit -m "feat: add extension hook points to eda, train, evaluate, deploy, preprocess commands"
```

---

### Task 6: Write Extension Protocol Documentation

Create a guide for extension authors documenting the protocol, hook points, and plugin structure.

**Files:**
- Create: `docs/extension-protocol.md`

- [ ] **Step 1: Write the extension protocol guide**

```markdown
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

## Hook Point Timing

All `after-*` hook points fire AFTER any reflection gates for that stage have passed. Your extension agent receives the final, gate-approved output — never intermediate pre-gate data.

## Versioning Contract

Hook point names are a versioned contract. The core plugin will NOT rename or remove hook points without a major version bump (e.g., 1.x → 2.0) and a deprecation notice in the changelog. You can depend on hook point names being stable within a major version.

## Error Handling

Extension agent failures at hook points do NOT block core workflows. The core logs a warning and continues. Extension-specific workflows (your own commands) should handle errors as needed.
```

- [ ] **Step 2: Commit**

```bash
git add docs/extension-protocol.md
git commit -m "docs: add extension protocol guide for extension authors"
```

---

### Task 7: Add Extension Routing Evals

Add eval cases that test the assigner's ability to route to extension agents (simulating installed extensions).

**Files:**
- Modify: `evals/routing_evals.json` (add extension routing test cases)

- [ ] **Step 1: Read the current routing evals**

Read `evals/routing_evals.json` to confirm the current structure and last ID.

- [ ] **Step 2: Add extension routing eval cases**

Append new eval cases that test extension agent routing. These simulate a scenario where an MMM extension is installed:

```json
{
  "id": 19,
  "name": "mmm-channel-attribution",
  "prompt": "Analyze the marketing spend data and determine channel attribution using media mix modeling",
  "expected_agent": "mmm-analyst",
  "rationale": "Keywords 'media mix modeling' and 'channel attribution' match mmm-analyst routing_keywords — extension agent should be routed via Priority 2.5"
},
{
  "id": 20,
  "name": "extension-does-not-override-core",
  "prompt": "The model accuracy dropped after the last data update, investigate the data quality",
  "expected_agent": "eda-analyst",
  "rationale": "Even with extensions installed, core Priority 2 rules match first — 'accuracy dropped' + 'data' routes to eda-analyst, not an extension agent"
}
```

- [ ] **Step 3: Commit**

```bash
git add evals/routing_evals.json
git commit -m "feat: add extension routing eval cases for assigner validation"
```

---

### Task 8: Bump Version and Update plugin.json

Update the plugin version to reflect the new extension protocol capability.

**Files:**
- Modify: `.claude-plugin/plugin.json` (version bump + keywords)

- [ ] **Step 1: Read plugin.json**

Read `.claude-plugin/plugin.json` to confirm current version.

- [ ] **Step 2: Bump version to 1.8.0 and add extension keywords**

Update version from current to `1.8.0`. Add `"extensible"`, `"extension-protocol"`, `"plugin-ecosystem"` to keywords array.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: bump to v1.8.0 — modular extension architecture"
```

---

### Task 9: Update Spec Status and Final Verification

Mark the spec as implemented and verify all changes are consistent.

**Files:**
- Modify: `docs/specs/2026-03-27-modular-extension-architecture-design.md` (status → Implemented)

- [ ] **Step 1: Verify all changes are consistent**

Read the modified files and check:
- Orchestrator references the same hook point names as team-coldstart and the spec
- Assigner tier 2.5 description matches the spec
- All 10 hook points are present in team-coldstart
- Individual commands have their correct hook points
- Extension protocol doc matches the spec
- ml_utils.py has no remaining hardcoded agent lists

- [ ] **Step 2: Update spec status**

Change `**Status:** Draft` to `**Status:** Implemented` in the spec document.

- [ ] **Step 3: Commit**

```bash
git add docs/specs/2026-03-27-modular-extension-architecture-design.md
git commit -m "docs: mark extension architecture spec as implemented"
```
