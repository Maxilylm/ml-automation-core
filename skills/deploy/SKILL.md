---
name: deploy
description: Deploy applications, dashboards, and models to various targets including local Docker, Snowflake, Streamlit Cloud, or cloud platforms. Works with any data application.
---

# Deployment

## When to Use
- Deploying trained models or dashboards to production
- Setting up Docker containers, cloud services, or Streamlit apps
- Creating inference APIs

## Supported Targets

| Target | Command | What It Does |
|--------|---------|-------------|
| Local Docker | `/deploy local` | Builds Docker image, starts docker-compose, verifies health |
| Snowflake | `/deploy snowflake` | Model Registry + Streamlit in Snowflake |
| Streamlit Cloud | `/deploy streamlit-cloud` | Community Cloud deployment |
| AWS | `/deploy aws` | ECS, Lambda, or SageMaker |
| GCP | `/deploy gcp` | Cloud Run or Vertex AI |

## Workflow

1. **Validate requirements** — Check model artifact exists, dependencies resolved
2. **Verify dashboard interactivity** — Ensure dashboard has live inference (if model exists), EDA deep dive, and what-if analysis tabs
3. **Package application** — Build Docker image or package for target
4. **Configure environment** — Set env vars, secrets, connection strings
5. **Deploy and verify** — Deploy to target, check health endpoints, test live inference endpoint
6. **Set up monitoring** — Logging, alerting, performance dashboards

## Agent Coordination

- **mlops-engineer** — Handles deployment infrastructure and registry
- **brutal-code-reviewer** — Reviews deployment code quality
- **frontend-ux-analyst** — Reviews dashboard UX (if deploying Streamlit)

## Report Bus Integration (v1.2.0)

Reads prior reports to populate deployment metadata. Writes deployment report:
```python
from ml_utils import save_agent_report
save_agent_report("deployer", {
    "status": "completed",
    "findings": {"target": "local", "url": "http://localhost:8000", "health": "ok"},
    "artifacts": ["Dockerfile", "docker-compose.yml", "app/main.py"]
})
```

## MLOps Registry (v1.3.0)

After deployment, registers the deployed model version in `model-registry.json` with deployment metadata (target, URL, timestamp). Use `/registry models` to inspect.

## Full Specification

See `commands/deploy.md` for complete deployment workflows, Dockerfile templates, and target-specific instructions.
