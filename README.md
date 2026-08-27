# PBI Lineage Backend

Standalone FastAPI backend for Power BI and Microsoft Fabric metadata discovery,
report definition retrieval, PBIR normalization, and future lineage/impact
analysis.

This backend is being split out from the original Streamlit-based PBI Lineage
Explorer so the application can evolve into a cleaner service-oriented
architecture.

## What This Service Does

Current capabilities:

- Starts Microsoft device-code authentication for local/backend testing.
- Stores short-lived in-memory auth sessions.
- Lists Power BI workspaces.
- Gets one Power BI workspace.
- Lists Power BI reports in a workspace.
- Gets one Power BI report.
- Lists report pages.
- Gets one report page.
- Lists Power BI semantic models/datasets in a workspace.
- Retrieves Fabric report definitions.
- Decodes and normalizes PBIR report definitions.
- Extracts visual titles, visual positions, visual types, page metadata, and
  semantic model references from PBIR.
- Extracts visual field references for columns, measures, hierarchies, sorts,
  filters, and projections.
- Retrieves Fabric semantic model definitions in TMDL/TMSL format.
- Exposes provider authentication/scope diagnostics.

Future capabilities:

- Parse semantic model definitions into tables, columns, measures,
  relationships, hierarchies, and expressions.
- Join report visual field usage to semantic model objects.
- Add XMLA metadata extraction.
- Add Snowflake lineage.
- Add impact analysis APIs.
- Add production-grade auth/session storage.
- Add observability and caching.

## Technology Stack

- Python 3.11+
- FastAPI
- Pydantic / Pydantic Settings
- httpx
- MSAL
- uv
- pytest / pytest-asyncio
- ruff
- Docker

## Quick Start

Install/sync dependencies:

```powershell
uv sync
```

Run the development server:

```powershell
uv run fastapi dev app/main.py
```

Default local docs:

```text
http://127.0.0.1:8000/docs
```

Run tests:

```powershell
uv run pytest
```

Run linting:

```powershell
uv run ruff check .
```

Build Docker image:

```powershell
docker build -t pbi-lineage-backend .
```

Run Docker container:

```powershell
docker run --rm -p 8000:8000 pbi-lineage-backend
```

## Environment

`.env.example`:

```text
APP_NAME=PBI Lineage Backend
APP_VERSION=0.1.0
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO
```

## API Overview

All endpoints are mounted under `/api/v1`.

### Health

```text
GET /api/v1/health
GET /api/v1/health/live
GET /api/v1/health/ready
```

### Authentication

```text
POST /api/v1/auth/microsoft/device/start
GET  /api/v1/auth/microsoft/device/status
GET  /api/v1/auth/microsoft/device/{session_id}/status
POST /api/v1/auth/microsoft/device/logout
```

Device auth status is intended to show:

- Overall auth status.
- Power BI connection result.
- Fabric connection result.
- Requested scopes.
- Granted scopes.
- Missing scopes.
- Provider error code.

### Power BI Metadata

```text
GET /api/v1/workspaces
GET /api/v1/workspaces/{workspace_id}
GET /api/v1/workspaces/{workspace_id}/reports
GET /api/v1/workspaces/{workspace_id}/reports/{report_id}
GET /api/v1/workspaces/{workspace_id}/reports/{report_id}/pages
GET /api/v1/workspaces/{workspace_id}/reports/{report_id}/pages/{page_name}
GET /api/v1/workspaces/{workspace_id}/semantic-models
```

### Fabric Definitions

```text
POST /api/v1/workspaces/{workspace_id}/reports/{report_id}/definition
POST /api/v1/workspaces/{workspace_id}/reports/{report_id}/definition/normalized
POST /api/v1/workspaces/{workspace_id}/semantic-models/{semantic_model_id}/definition
```

The semantic model definition endpoint is part of the current uncommitted phase.

## Folder Structure

```text
app/
  api/
  clients/
  core/
  domain/
  schemas/
  services/
  utils/
tests/
  api/
  unit/
```

## File And Folder Purpose

### `app/main.py`

Application factory and FastAPI entrypoint. It configures:

- App metadata.
- CORS middleware.
- Request logging middleware.
- Request ID middleware.
- Exception handlers.
- API router mounting.

### `app/api`

FastAPI routing layer.

- `app/api/router.py`
  - Combines all v1 routers under health, auth, and workspaces.
- `app/api/v1/health.py`
  - Health, liveness, and readiness endpoints.
- `app/api/v1/auth.py`
  - Microsoft device auth start/status/logout endpoints.
  - In-progress scope diagnostics for Power BI and Fabric status.
- `app/api/v1/workspaces.py`
  - Workspace, report, page, semantic model, report definition, normalized
    report definition, and semantic model definition endpoints.
- `app/api/dependencies/credentials.py`
  - FastAPI dependencies for extracting Power BI and Fabric access tokens from
    the auth session cookie.

### `app/clients`

Provider HTTP clients. These files should know provider URL details but should
not contain business normalization logic.

- `provider_http_client.py`
  - Shared HTTP behavior and provider error mapping.
- `powerbi_client.py`
  - Power BI REST API client.
- `fabric_client.py`
  - Microsoft Fabric API client.
  - Handles report and semantic model definition endpoints and long-running
    operation result APIs.
- `snowflake_client.py`
  - Placeholder for future Snowflake integration.

### `app/core`

Cross-cutting application infrastructure.

- `config.py`
  - Environment-backed settings.
- `auth_session.py`
  - Auth cookie name and max-age constants.
- `microsoft_auth.py`
  - Microsoft authority/resource/scope constants and scope diagnostic helpers.
- `exceptions.py`
  - Application exception classes.
- `error_handlers.py`
  - FastAPI exception handlers and consistent error response shape.
- `logging.py`
  - JSON logging and sensitive value redaction.
- `request_id.py`
  - Request ID middleware and `X-Request-ID` response propagation.
- `request_context.py`
  - Context variable for request IDs.
- `request_logging.py`
  - Structured request completion logs.
- `security.py`
  - Reserved for future security helpers.

### `app/schemas`

Pydantic API contracts.

- `workspace.py`
  - Workspace list/detail responses.
- `report.py`
  - Report list/detail responses.
- `report_page.py`
  - Report page list/detail responses.
- `semantic_model.py`
  - Semantic model list responses.
- `report_definition.py`
  - Raw Fabric report definition response.
- `semantic_model_definition.py`
  - Raw Fabric semantic model definition response.
- `normalized_report_definition.py`
  - API shape for normalized PBIR reports, pages, visuals, positions, semantic
    model references, and visual field references.
- `auth.py`
  - Microsoft auth requests, device flow responses, provider connection status,
    and scope diagnostics.
- `error.py`
  - Structured API error response models.
- `exceptions.py`
  - Older duplicate exception schema/module. Active app code uses
    `app.core.exceptions`.

### `app/services`

Business logic layer. Routes call services; services call clients.

- `workspace_service.py`
  - Maps Power BI workspace payloads.
- `report_service.py`
  - Maps Power BI reports and pages.
- `semantic_model_service.py`
  - Maps Power BI datasets/semantic models.
- `report_definition_service.py`
  - Retrieves Fabric report definitions and handles long-running operations.
- `semantic_model_definition_service.py`
  - Retrieves Fabric semantic model definitions and handles long-running
    operations.
- `report_definition_decoder.py`
  - Decodes structural JSON definition parts from base64 payloads.
- `report_definition_normalizer.py`
  - Normalizes PBIR report definitions into pages, visuals, positions, titles,
    semantic model references, and warnings.
- `visual_field_reference_extractor.py`
  - Extracts visual-to-field references from PBIR visual semantic queries.
- `services/auth/device_auth_store.py`
  - In-memory device auth session/token store.
- `services/auth/microsoft_device_auth_service.py`
  - MSAL device-code auth, token validation, Fabric silent auth attempt, and
    scope diagnostic population.
- `services/auth/powerbi_auth_service.py`
  - Power BI token validation wrapper.
- `services/auth/fabric_auth_service.py`
  - Fabric token validation wrapper.
- `services/auth/microsoft_auth_service.py`
  - Commented PKCE preparation helper from earlier auth design.
- `services/auth/snowflake_auth_service.py`
  - Placeholder for future Snowflake auth.

### `tests`

Automated tests.

- `tests/conftest.py`
  - FastAPI test client fixture.
- `tests/api/test_auth.py`
  - Device auth route/status/logout behavior.
- `tests/api/test_report_resources.py`
  - Report route behavior with dependency overrides.
- `tests/unit/test_microsoft_auth.py`
  - Scope diagnostic helper tests.
- `tests/unit/test_report_service.py`
  - Report service mapping/validation.
- `tests/unit/test_semantic_model_service.py`
  - Semantic model service mapping/validation.
- `tests/unit/test_report_definition_service.py`
  - Fabric report definition immediate and long-running behavior.
- `tests/unit/test_semantic_model_definition_service.py`
  - Fabric semantic model definition behavior.
- `tests/unit/test_report_definition_decoder.py`
  - Base64/JSON definition decoding.
- `tests/unit/test_report_definition_normalizer.py`
  - PBIR normalization behavior.
- `tests/unit/test_visual_field_reference_extractor.py`
  - Visual semantic field extraction.
- `tests/unit/test_logging.py`
  - Sensitive value redaction.

## Phase History

This timeline follows the repository milestone history provided by the
maintainer. Commit IDs and author details are intentionally omitted.

| Date | Milestone | Status | Summary |
| --- | --- | --- | --- |
| Aug 18, 2026 | Backend initialization | Completed | Initialized the FastAPI backend. |
| Aug 18, 2026 | Backend setup guide | Completed | Added the backend setup guide. |
| Aug 18, 2026 | Phase 1 | Completed | Completed the initial backend foundation. |
| Aug 18, 2026 | Phase 2.3 | Completed | Continued backend foundation work. |
| Aug 21, 2026 | Phase 2.6 | Completed | Continued backend foundation work. |
| Aug 21, 2026 | Phase 2.7 | Completed | Continued backend foundation work. |
| Aug 24, 2026 | Phase 3.1 | Completed | Added workspace discovery and authentication. |
| Aug 24, 2026 | Phase 3.2 | Completed | Added report and semantic model listing. |
| Aug 24, 2026 | Phase 3.2 test/refinement | Completed | Added tests and refinements for report and semantic model listing. |
| Aug 26, 2026 | Phase 3.3 | Completed | Added Fabric report definition retrieval. |
| Aug 26, 2026 | Phase 3.4 | Completed | Added report definition decoding and normalization. |
| Aug 26, 2026 | Phase 3.5 | Completed | Added visual semantic query and field reference extraction. |
| Aug 28, 2026 | Phase 3.6 | Completed locally | Stabilized auth diagnostics and Fabric scope handling. |
| Aug 28, 2026 | Phase 3.7 | Completed locally | Finalized semantic model definition retrieval coverage. |

### Latest Completed Phase

Phase 3.7 is the latest completed local phase. It finalized semantic model
definition retrieval by covering immediate Fabric responses, long-running
operation responses, failed operation statuses, invalid payload handling, Fabric
client URL/query construction, API route wiring, and `payloadType` response
serialization.

### Next Phase

Phase 3.8 - Parse Semantic Model Definition is the next phase.

Recommended Phase 3.8 work:

- Decode TMDL/TMSL semantic model definition parts.
- Extract tables, columns, measures, relationships, hierarchies, and
  expressions into response schemas.
- Keep semantic model parsing separate from PBIR report normalization.
- Add focused tests for TMDL/TMSL parsing and invalid definition parts.

## Current Review Notes

Phase 3.6 and Phase 3.7 are locally verified with Ruff and pytest. The only
current test-suite warning is a third-party FastAPI/TestClient warning about
Starlette's `httpx` integration.

## Development Notes

- Keep API route handlers thin.
- Put provider HTTP details in `app/clients`.
- Put mapping, polling, decoding, and normalization in `app/services`.
- Keep response contracts in `app/schemas`.
- Use `AppException` subclasses for expected failures.
- Do not log access tokens, decoded payload values, authorization headers, or
  sensitive query strings.
- For Fabric definition changes, test both `200` immediate and `202`
  long-running operation paths.
- For PBIR normalization changes, use small encoded JSON fixture parts.
- Treat locally decoded JWT scopes as diagnostics only.
