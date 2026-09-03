# PBI Lineage Backend — Setup Guide

This document records the initial setup and deployment-ready foundation for the **PBI Lineage Backend** project.

The backend is being built as a standalone **FastAPI** service, separate from the existing Streamlit-based PBI Lineage Explorer frontend/application.

---

## 1. Project Goals

The backend should be:

- Built from scratch as an independent project.
- Based on **Python 3.11**.
- Implemented using **FastAPI**.
- Managed with **uv** for dependencies and virtual environments.
- Structured for maintainability as the application grows.
- Ready for local development and production deployment.
- Containerized using **Docker**.
- Configuration-driven using environment variables.
- Stateless so it can scale horizontally.
- Stored in an independent GitHub repository named:

```text
PBI-Lineage-Backend
```

The repository display name can be referred to as:

```text
PBI Lineage Backend
```

---

# 2. Technology Stack

Initial stack:

```text
Python 3.11
FastAPI
Pydantic Settings
uv
Pytest
pytest-asyncio
Ruff
Docker
Git
GitHub
```

Future integrations will include:

```text
Power BI REST APIs
Microsoft Fabric APIs
XMLA
PBIR parsing
Snowflake
PowerAI
Caching
Authentication / Authorization
Observability
```

These integrations are intentionally not added during the initial foundation setup.

---

# 3. Prerequisites

Open PowerShell and verify:

```powershell
python --version
git --version
```

The backend will standardize on:

```text
Python 3.11
```

## Install uv

Recommended Windows installation:

```powershell
winget install --id=astral-sh.uv -e
```

Alternative:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, restart the terminal and verify:

```powershell
uv --version
```

---

# 4. Create the Project Directory

Navigate to the directory where backend projects are stored.

Example:

```powershell
cd D:\Projects
```

Create the repository folder:

```powershell
mkdir PBI-Lineage-Backend
cd PBI-Lineage-Backend
```

Initial structure:

```text
PBI-Lineage-Backend/
```

---

# 5. Initialize the Python Project

Run:

```powershell
uv init --bare
```

`--bare` is used because the project structure will be created manually instead of generating an example application.

Expected initial result:

```text
PBI-Lineage-Backend/
└── pyproject.toml
```

---

# 6. Configure Python 3.11

Install Python 3.11 through uv:

```powershell
uv python install 3.11
```

Pin the project:

```powershell
uv python pin 3.11
```

Verify:

```powershell
uv run python --version
```

Expected:

```text
Python 3.11.x
```

A `.python-version` file should now exist.

---

# 7. Install FastAPI

Install FastAPI without the FastAPI Cloud CLI:

```powershell
uv add "fastapi[standard-no-fastapi-cloud-cli]"
```

This also provides the FastAPI CLI and Uvicorn-related runtime dependencies required to run the application.

---

# 8. Install Configuration Library

Install Pydantic Settings:

```powershell
uv add pydantic-settings
```

This will later manage:

- Environment variables
- Power BI settings
- Fabric settings
- XMLA settings
- Snowflake settings
- CORS configuration
- Authentication configuration
- Application configuration

---

# 9. Install Development Dependencies

Run:

```powershell
uv add --dev pytest pytest-asyncio ruff
```

Purpose:

```text
pytest          -> Unit, integration, and API tests
pytest-asyncio  -> Async test support
ruff            -> Linting and code-quality checks
```

---

# 10. Synchronize Dependencies

Run:

```powershell
uv sync
```

Inspect installed packages:

```powershell
uv tree
```

Important project dependency files:

```text
pyproject.toml
uv.lock
```

`uv.lock` must be committed to Git because this is an application and reproducible deployments are required.

---

# 11. Create Backend Folder Structure

Create the directories:

```powershell
mkdir app
mkdir app\api
mkdir app\api\v1
mkdir app\core
mkdir app\schemas
mkdir app\services
mkdir app\clients
mkdir app\domain
mkdir app\utils

mkdir tests
mkdir tests\unit
mkdir tests\integration
mkdir tests\api

mkdir .github
mkdir .github\workflows
```

Create Python package files:

```powershell
New-Item app\__init__.py
New-Item app\api\__init__.py
New-Item app\api\v1\__init__.py
New-Item app\core\__init__.py
New-Item app\schemas\__init__.py
New-Item app\services\__init__.py
New-Item app\clients\__init__.py
New-Item app\domain\__init__.py
New-Item app\utils\__init__.py
New-Item tests\__init__.py
```

Create initial source files:

```powershell
New-Item app\main.py
New-Item app\api\router.py
New-Item app\api\v1\health.py

New-Item app\core\config.py
New-Item app\core\exceptions.py
New-Item app\core\logging.py
```

Create root configuration files:

```powershell
New-Item .env.example
New-Item .gitignore
New-Item .dockerignore
New-Item Dockerfile
New-Item README.md
New-Item setup.md
```

---

# 12. Expected Project Structure

```text
PBI-Lineage-Backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   │
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── schemas/
│   │   └── __init__.py
│   │
│   ├── services/
│   │   └── __init__.py
│   │
│   ├── clients/
│   │   └── __init__.py
│   │
│   ├── domain/
│   │   └── __init__.py
│   │
│   └── utils/
│       └── __init__.py
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── .github/
│   └── workflows/
│
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── Dockerfile
├── README.md
├── setup.md
├── pyproject.toml
└── uv.lock
```

---

# 13. Configure pyproject.toml

The project metadata should be similar to:

```toml
[project]
name = "pbi-lineage-backend"
version = "0.1.0"
description = "FastAPI backend for PBI Lineage Explorer"
readme = "README.md"
requires-python = ">=3.11,<3.12"
```

Dependencies should normally be managed using `uv add` and `uv remove` rather than manually editing dependency versions.

Example:

```powershell
uv add <library>
```

Remove:

```powershell
uv remove <library>
```

Add the FastAPI application entrypoint:

```toml
[tool.fastapi]
entrypoint = "app.main:app"
```

This allows the application to be started without repeatedly specifying the Python file.

---

# 14. Application Configuration

File:

```text
app/core/config.py
```

Initial implementation:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PBI Lineage Backend"
    app_version: str = "0.1.0"
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Later this will be expanded for Power BI, Fabric, XMLA, Snowflake, authentication, CORS, caching, and other deployment configuration.

---

# 15. Environment Configuration

Create:

```text
.env.example
```

Initial values:

```env
APP_NAME=PBI Lineage Backend
APP_VERSION=0.1.0
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
```

For local development:

```powershell
Copy-Item .env.example .env
```

Important rules:

```text
.env.example -> committed to Git
.env         -> never committed to Git
```

Production secrets should be supplied by the deployment platform rather than copied into the repository or Docker image.

Future sensitive settings may include:

```text
POWERBI_TENANT_ID
POWERBI_CLIENT_ID
POWERBI_CLIENT_SECRET

SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PRIVATE_KEY

OPENAI_API_KEY
```

None of these should ever be hard-coded.

---

# 16. Health Endpoints

Because the backend will be deployed, three health endpoints are defined.

```text
GET /api/v1/health
GET /api/v1/health/live
GET /api/v1/health/ready
```

## General Health

Returns basic service information.

Example:

```json
{
  "status": "ok",
  "service": "PBI Lineage Backend",
  "version": "0.1.0"
}
```

## Liveness

Used to check whether the FastAPI process is alive.

Example:

```json
{
  "status": "alive"
}
```

## Readiness

Used by the deployment platform to determine whether the instance can receive traffic.

Example:

```json
{
  "status": "ready"
}
```

Readiness should not make expensive calls to Power BI, XMLA, or Snowflake every time it is called.

---

# 17. Health Router

File:

```text
app/api/v1/health.py
```

Implementation:

```python
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()

settings = get_settings()


@router.get("")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    return {
        "status": "alive",
    }


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    return {
        "status": "ready",
    }
```

---

# 18. Central API Router

File:

```text
app/api/router.py
```

Implementation:

```python
from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)
```

This gives:

```text
/api/v1/health
/api/v1/health/live
/api/v1/health/ready
```

---

# 19. FastAPI Application

File:

```text
app/main.py
```

Initial implementation:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    return app


app = create_app()
```

CORS origins are intentionally not hard-coded yet.

Later they should come from environment variables.

---

# 20. Run Locally

Development command:

```powershell
uv run fastapi dev
```

Development mode provides automatic reload.

Do not use reload mode for production.

Expected local server:

```text
http://127.0.0.1:8000
```

Verify:

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/api/v1/health/live
http://127.0.0.1:8000/api/v1/health/ready
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

---

# 21. Production Run Command

Production should use:

```powershell
uv run fastapi run --port 8000
```

Do not deploy with:

```text
fastapi dev
```

and do not enable:

```text
--reload
```

in production.

---

# 22. Git Ignore Configuration

File:

```text
.gitignore
```

Recommended contents:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environments
.venv/
venv/
env/

# Environment variables
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Ruff
.ruff_cache/

# Type checking
.mypy_cache/

# Build
build/
dist/
*.egg-info/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary
tmp/
temp/
*.tmp
```

Important:

```text
uv.lock
```

must NOT be ignored.

---

# 23. Docker Ignore Configuration

File:

```text
.dockerignore
```

Recommended contents:

```dockerignore
.git
.github

.venv
venv

.env
.env.*
!.env.example

__pycache__
*.pyc
*.pyo
*.pyd

.pytest_cache
.ruff_cache
.mypy_cache

.coverage
htmlcov

.idea
.vscode

.DS_Store
Thumbs.db

tests

*.log
logs

README.md
```

Important exclusions:

```text
.env
.venv
.git
```

The local virtual environment must never be copied into the production Linux container.

---

# 24. Dockerfile

Initial deployment-ready Dockerfile:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --locked \
    --no-dev \
    --no-install-project

COPY app ./app

RUN uv sync \
    --locked \
    --no-dev

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "fastapi", "run", "--port", "8000"]
```

This is an initial Dockerfile and may be updated later when XMLA or other native system dependencies are introduced.

---

# 25. Build Docker Image

Run:

```powershell
docker build -t pbi-lineage-backend .
```

---

# 26. Run Docker Container

PowerShell:

```powershell
docker run `
  --rm `
  -p 8000:8000 `
  --env-file .env `
  pbi-lineage-backend
```

Verify:

```text
http://localhost:8000/api/v1/health
http://localhost:8000/api/v1/health/live
http://localhost:8000/api/v1/health/ready
http://localhost:8000/docs
```

The backend should behave the same when run:

```text
locally using uv
```

and:

```text
inside Docker
```

---

# 27. Deployment Architecture

The intended production flow is:

```text
Developer
   |
   | git push
   v
GitHub
   |
   v
GitHub Actions
   |
   +--> Lint
   +--> Tests
   +--> Docker Build
   +--> Security Checks
   |
   v
Container Registry
   |
   v
Deployment Platform
   |
   v
FastAPI Container
   |
   v
Power BI / Fabric / XMLA / Snowflake
```

The exact deployment target will be selected later.

Possible deployment environments include:

```text
Azure Container Apps
Azure App Service
AWS ECS
Kubernetes
Virtual Machine
Other managed container platforms
```

---

# 28. Deployment Design Principles

## 28.1 Stateless Backend

Do not use global application state for user-specific information.

Avoid:

```python
current_user = ...
current_workspace = ...
current_report = ...
```

Do not recreate Streamlit's:

```python
st.session_state
```

inside FastAPI.

Requests should follow:

```text
HTTP Request
     |
     v
Authentication Context
     |
     v
API Router
     |
     v
Service
     |
     v
Response
```

Shared/persistent state should later live in appropriate external stores such as:

```text
Redis
Database
Object storage
```

---

## 28.2 Environment-Driven Configuration

Do not hard-code environment-specific values.

Bad:

```python
cors_origin = "http://localhost:8501"
tenant_id = "..."
snowflake_account = "..."
```

Correct approach:

```text
Environment Variable
        |
        v
Pydantic Settings
        |
        v
Application
```

---

## 28.3 Secrets Must Stay Outside Docker Images

Never do:

```dockerfile
ENV POWERBI_CLIENT_SECRET=...
```

Never do:

```dockerfile
COPY .env .
```

Correct model:

```text
Docker image
     |
     +--> Application code
     +--> Dependencies

Deployment platform
     |
     +--> Runtime secrets
     +--> Runtime configuration
```

---

## 28.4 Production Logging

Do not rely on log files stored inside the container.

Avoid:

```text
application.log
server.log
```

Production logging should initially go to:

```text
stdout
stderr
```

The deployment platform can collect these logs into systems such as:

```text
Azure Monitor
CloudWatch
ELK
Datadog
Grafana/Loki
```

Structured JSON logging can be introduced during the next backend foundation step.

---

## 28.5 HTTPS

FastAPI itself should not be responsible for managing public TLS certificates.

Expected architecture:

```text
Internet
   |
   | HTTPS
   v
Gateway / Load Balancer / Ingress
   |
   | internal HTTP
   v
FastAPI :8000
```

---

## 28.6 CORS

Do not permanently use:

```python
allow_origins = ["*"]
```

especially once credentials or authentication headers are involved.

CORS should later be environment-driven.

Development example:

```env
CORS_ORIGINS=http://localhost:8501
```

Production example:

```env
CORS_ORIGINS=https://pbi.example.com
```

---

## 28.7 Worker Strategy

Initially use:

```text
1 FastAPI/Uvicorn process per container
```

Do not hard-code multiple workers into the application.

A container platform can scale horizontally:

```text
Container 1
Container 2
Container 3
```

If the application is deployed directly to a single VM, worker counts can later be configured according to CPU and memory resources.

This is particularly important because PBI Lineage processing may become memory intensive due to:

```text
XMLA metadata
PBIR definitions
semantic models
DAX dependencies
lineage graphs
impact graphs
Snowflake metadata
```

---

# 29. Initialize Git Repository

From the project root:

```powershell
git init
```

Rename the default branch:

```powershell
git branch -M main
```

Check files:

```powershell
git status
```

The following should NOT be included:

```text
.env
.venv/
```

The following should be committed:

```text
app/
tests/
.github/
.env.example
.dockerignore
.gitignore
.python-version
Dockerfile
README.md
setup.md
pyproject.toml
uv.lock
```

---

# 30. Create First Commit

Run:

```powershell
git add .
```

Review:

```powershell
git status
```

Commit:

```powershell
git commit -m "chore: initialize FastAPI backend"
```

---

# 31. Create GitHub Repository

Create a new GitHub repository named:

```text
PBI-Lineage-Backend
```

Suggested description:

```text
FastAPI backend for PBI Lineage Explorer
```

Initial recommendation:

```text
Visibility: Private
```

Because the local repository is already initialized, do not ask GitHub to automatically create:

```text
README
.gitignore
License
```

This avoids creating unrelated initial history.

---

# 32. Connect Local Git Repository to GitHub

GitHub will provide a remote URL such as:

```text
https://github.com/<USERNAME>/PBI-Lineage-Backend.git
```

Add it:

```powershell
git remote add origin https://github.com/<USERNAME>/PBI-Lineage-Backend.git
```

Verify:

```powershell
git remote -v
```

Push:

```powershell
git push -u origin main
```

---

# 33. Phase 1 Verification Checklist

Before moving to Power BI integration, verify all of the following.

- [ ] Project directory created.
- [ ] Independent `PBI-Lineage-Backend` repository created.
- [ ] Python 3.11 installed and pinned.
- [ ] uv installed.
- [ ] `pyproject.toml` created.
- [ ] `uv.lock` created and committed.
- [ ] FastAPI installed.
- [ ] Pydantic Settings installed.
- [ ] Pytest installed.
- [ ] pytest-asyncio installed.
- [ ] Ruff installed.
- [ ] Application package structure created.
- [ ] `/api/v1` routing structure created.
- [ ] General health endpoint works.
- [ ] Liveness endpoint works.
- [ ] Readiness endpoint works.
- [ ] Swagger UI works.
- [ ] ReDoc works.
- [ ] `.env` excluded from Git.
- [ ] `.venv` excluded from Git and Docker.
- [ ] Dockerfile created.
- [ ] Docker image builds successfully.
- [ ] Docker container starts successfully.
- [ ] Health endpoints work from inside Docker.
- [ ] Local Git repository initialized.
- [ ] GitHub repository created.
- [ ] Initial code pushed to `main`.

---

# 34. Standard Development Commands

## Start development server

```powershell
uv run fastapi dev
```

## Start production mode locally

```powershell
uv run fastapi run --port 8000
```

## Synchronize dependencies

```powershell
uv sync
```

## View dependency tree

```powershell
uv tree
```

## Run tests

```powershell
uv run pytest
```

## Run Ruff

```powershell
uv run ruff check .
```

## Build Docker image

```powershell
docker build -t pbi-lineage-backend .
```

## Run Docker image

```powershell
docker run `
  --rm `
  -p 8000:8000 `
  --env-file .env `
  pbi-lineage-backend
```

## Check Git status

```powershell
git status
```

## Commit changes

```powershell
git add .
git commit -m "<commit message>"
```

## Push changes

```powershell
git push
```

---

# 35. Backend Architectural Direction

As the PBI Lineage functionality is separated from the existing application, the backend should follow this layering:

```text
Frontend
   |
   | HTTP / JSON
   v
FastAPI API Layer
   |
   v
Service Layer
   |
   v
Domain / Lineage Layer
   |
   v
Infrastructure Clients
   |
   +--> Power BI
   +--> Fabric
   +--> XMLA
   +--> Snowflake
```

FastAPI routes should remain thin.

Example:

```python
@router.get("/lineage")
async def get_lineage(...):
    return await lineage_service.get_lineage(...)
```

Heavy lineage, parsing, API access, or transformation logic should not be implemented directly inside route handlers.

---

# 36. Planned Next Foundation Work

Before implementing Power BI APIs, the backend foundation should next add:

1. Structured application logging.
2. Global exception handling.
3. Standard API response/error format.
4. Request correlation/request IDs.
5. Environment-aware CORS.
6. FastAPI lifespan/startup management.
7. API tests for health endpoints.
8. Ruff configuration.
9. Pytest configuration.
10. Docker health checks.
11. GitHub Actions CI workflow.
12. Production configuration validation.

Only after this foundation is stable should the backend begin extracting:

```text
Power BI authentication
Power BI workspace discovery
Report discovery
Semantic model discovery
XMLA metadata
PBIR parsing
Lineage
Impact analysis
Snowflake lineage
PowerAI
```

---

# 37. Core Project Rule

All future backend work should follow this rule:

> Anything added to the PBI Lineage Backend must work consistently on a developer machine and inside a production Linux container, with environment-specific configuration supplied externally.

This prevents later redesign when the application moves from development into production deployment.
