---
name: deploy
description: "Deploy applications, dashboards, and models to various targets including local Docker, Snowflake, Streamlit Cloud, or cloud platforms. Works with any data application."
user_invocable: true
aliases: ["ship", "publish", "release"]
---

# Deploy Skill - Application Deployment

You are deploying the data application (API + dashboard) to a specified target environment.

## Overview

The `/deploy` command deploys applications to:
- **local** - Docker containers on local machine (API + Streamlit dashboard)
- **snowflake** - Snowflake Model Registry + Streamlit in Snowflake
- **streamlit-cloud** - Streamlit Community Cloud
- **aws** - AWS deployment (ECS, Lambda, SageMaker)
- **gcp** - Google Cloud deployment (Cloud Run, Vertex AI)

## Usage

```bash
# Deploy to local Docker
/deploy local

# Deploy to Snowflake
/deploy snowflake

# Deploy Streamlit dashboard to Snowflake
/deploy streamlit-sis

# Deploy with specific model version
/deploy snowflake --model-version v2

# Deploy to AWS
/deploy aws --region us-east-1
```

## Deployment Targets

### Local Docker Deployment

**Command:** `/deploy local`

**What it does:**
1. Builds Docker image from Dockerfile
2. Starts services with docker-compose
3. Verifies health checks
4. Reports service URLs

**Steps:**
```bash
# Build the Docker image
cd {Path}
docker build -t ml-model:latest -f deploy/docker/Dockerfile .

# Start services
cd deploy/docker
docker-compose up -d

# Verify health
curl http://localhost:8000/health

# Check logs
docker-compose logs -f ml-api
```

**Output:**
```markdown
## Local Deployment Complete

### Services Running
| Service | URL | Status |
|---------|-----|--------|
| ML API | http://localhost:8000 | ✅ Healthy |
| Streamlit | http://localhost:8501 | ✅ Running |
| Prometheus | http://localhost:9090 | ✅ Running |
| Grafana | http://localhost:3000 | ✅ Running |

### Quick Test
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"Pclass": 1, "Sex": "female", "Age": 29, "SibSp": 0, "Parch": 0, "Fare": 211.34, "Embarked": "S"}'
```

### Useful Commands
- Stop: `docker-compose down`
- Logs: `docker-compose logs -f`
- Rebuild: `docker-compose up -d --build`
```

### Snowflake Deployment

**Command:** `/deploy snowflake`

**Prerequisites:**
- Snowflake account configured
- Environment variables set:
  - SNOWFLAKE_ACCOUNT
  - SNOWFLAKE_USER
  - SNOWFLAKE_PASSWORD
  - SNOWFLAKE_ROLE
  - SNOWFLAKE_WAREHOUSE
  - SNOWFLAKE_DATABASE

**What it does:**
1. Connects to Snowflake
2. Runs setup SQL (if not already done)
3. Uploads data to Snowflake stage
4. Runs preprocessing in Snowpark
5. Trains model using Snowpark ML
6. Registers model in Model Registry
7. Creates prediction UDFs

**Steps:**
```python
from src.snowflake_utils import create_session
from src.snowpark_preprocessing import run_and_save
from src.snowpark_model import train_and_register

# Connect
session = create_session()

# Run setup SQL (first time only)
# snowsql -f deploy/snowflake/setup.sql

# Preprocess data
run_and_save(session, "RAW.TITANIC", "STAGING.TITANIC_PROCESSED")

# Train and register model
result = train_and_register(
    session,
    train_table="STAGING.TITANIC_PROCESSED",
    model_name="TITANIC_SURVIVAL_MODEL",
    version="v1"
)

# Create UDFs
# snowsql -f deploy/snowflake/udfs.sql

session.close()
```

**Output:**
```markdown
## Snowflake Deployment Complete

### Model Registry
- **Model Name**: TITANIC_SURVIVAL_MODEL
- **Version**: v1
- **Status**: ✅ Registered

### Model Metrics
| Metric | Value |
|--------|-------|
| Accuracy | 85.2% |
| Precision | 83.1% |
| Recall | 79.4% |
| F1 Score | 81.2% |

### UDFs Created
- `MODELS.PREDICT_SURVIVAL()` - Single prediction
- `MODELS.PREDICT_SURVIVAL_PROBA()` - With probability
- `MODELS.PREDICT_FROM_RAW()` - From raw input
- `MODELS.BATCH_PREDICT()` - Batch procedure

### Usage Example
```sql
SELECT MODELS.PREDICT_FROM_RAW(1, 'female', 29, 0, 0, 211.34, 'S');
```
```

### Streamlit in Snowflake Deployment

**Command:** `/deploy streamlit-sis`

**What it does:**
1. Validates Streamlit app code
2. Deploys to Snowflake
3. Sets permissions
4. Returns app URL

**Steps:**
```bash
# Deploy using Snowflake CLI
snowcli streamlit deploy \
    --database ML_PROJECT \
    --schema ANALYTICS \
    --name TITANIC_DASHBOARD \
    --file deploy/snowflake/streamlit/app.py \
    --replace
```

**Output:**
```markdown
## Streamlit in Snowflake Deployment Complete

### Dashboard
- **Name**: TITANIC_DASHBOARD
- **Database**: ML_PROJECT
- **Schema**: ANALYTICS
- **Status**: ✅ Deployed

### Access
Open Snowsight and navigate to:
`ML_PROJECT.ANALYTICS.TITANIC_DASHBOARD`

Or use direct URL (if available in your Snowflake account).

### Features
- Real-time survival prediction
- Model performance metrics
- Data insights and visualizations
- Interactive data exploration
```

### AWS Deployment

**Command:** `/deploy aws`

**What it does:**
1. Packages model for SageMaker
2. Creates model endpoint
3. Sets up Lambda for API Gateway (optional)
4. Configures CloudWatch monitoring

**Prerequisites:**
- AWS CLI configured
- IAM permissions for SageMaker, Lambda, API Gateway

**Note:** This is a placeholder for AWS deployment. Full implementation requires AWS SDK setup.

### GCP Deployment

**Command:** `/deploy gcp`

**What it does:**
1. Uploads model to Cloud Storage
2. Deploys to Vertex AI
3. Creates prediction endpoint
4. Sets up Cloud Monitoring

**Prerequisites:**
- gcloud CLI configured
- Service account with appropriate permissions

**Note:** This is a placeholder for GCP deployment. Full implementation requires GCP SDK setup.

### Extension Hook Point: before-deploy

Scan for extension agents with `hooks_into` containing "before-deploy":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "before-deploy"
3. Spawn each matching agent with current report context
4. On failure: log warning, continue

## Deployment Checklist

Before deploying, verify:

### Model Readiness
- [ ] Model trained and evaluated
- [ ] Model saved to models/ directory (joblib/pkl format)
- [ ] Preprocessing pipeline saved alongside model (if applicable)
- [ ] Metrics meet threshold (accuracy > 80%)

### Dashboard Interactivity
- [ ] Dashboard has 6 tabs (Overview, EDA Deep Dive, Model Performance, Live Inference, What-If, Data Explorer)
- [ ] Live inference tab loads model and accepts user inputs
- [ ] EDA deep dive shows distributions, correlations, missing values, outliers
- [ ] What-if analysis allows feature manipulation with real-time prediction updates
- [ ] Dashboard works gracefully when model artifacts are missing (degraded mode)

### Code Readiness
- [ ] All tests passing
- [ ] Coverage > 80%
- [ ] API endpoints tested
- [ ] Health check implemented

### Configuration
- [ ] Environment variables set
- [ ] Credentials configured (not in code)
- [ ] Logging configured

### Documentation
- [ ] API documentation updated
- [ ] Deployment instructions documented
- [ ] Rollback procedure documented

## Rollback Procedures

### Local Docker
```bash
# Stop current deployment
docker-compose down

# Deploy previous version
docker-compose up -d --build
```

### Snowflake
```sql
-- Rollback to previous model version
ALTER MODEL TITANIC_SURVIVAL_MODEL
SET DEFAULT VERSION = 'v_previous';

-- Or delete problematic version
DROP MODEL VERSION TITANIC_SURVIVAL_MODEL VERSION v_current;
```

### Extension Hook Point: after-deploy

Scan for extension agents with `hooks_into` containing "after-deploy":
1. Use Glob: `.claude/plugins/*/agents/*.md`, `~/.claude/plugins/*/agents/*.md`
2. Read frontmatter — select agents with `extends: ml-automation` and `hooks_into` including "after-deploy"
3. Spawn each matching agent with current report context
4. On failure: log warning, continue

## Invoke Agents

This skill coordinates with:
- **mlops-engineer** - For Docker/cloud deployments
- **frontend-ux-analyst** - For dashboard review
- **brutal-code-reviewer** - For deployment code review

After deployment, verify:
1. Health check passes
2. Sample predictions work
3. Monitoring is active
4. Logs are flowing
