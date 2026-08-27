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
- Parses TMDL semantic model definitions into tables, columns, measures,
  relationships, and hierarchies.
- Carries semantic model source-path evidence into lineage matches.
- Extracts XMLA semantic model metadata through an ADOMD adapter when the host
  has the Analysis Services client libraries configured.
- Adds lineage diagnostics with match confidence, candidate suggestions, and
  summary counts by status and object type.
- Exposes provider authentication/scope diagnostics.
- Validates Fabric report definition formats separately from semantic model
  definition formats.
- Surfaces provider error details for Fabric request and operation failures.

Future capabilities:

- Improve semantic model parser coverage for more TMDL shapes.
- Validate XMLA extraction against live Power BI/Fabric capacities.
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
XMLA_TENANT_NAME=myorg
XMLA_ADOMD_DLL_PATH=
XMLA_ACCESS_TOKEN_MINUTES=55
```

XMLA live extraction requires `pythonnet` plus the Microsoft Analysis Services
ADOMD client library on the host. If the ADOMD assembly is not discoverable,
set `XMLA_ADOMD_DLL_PATH` to the installed
`Microsoft.AnalysisServices.AdomdClient.dll` path.

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
POST /api/v1/workspaces/{workspace_id}/semantic-models/{semantic_model_id}/definition/parsed
POST /api/v1/workspaces/{workspace_id}/reports/{report_id}/semantic-lineage
```

Report definition endpoints accept `format=PBIR` or `format=PBIR-Legacy`.
The default is `PBIR`.

Semantic model definition endpoints accept `format=TMDL` or `format=TMSL`.
The default is `TMDL`.

The semantic-lineage endpoint returns visual field matches, source-path
evidence, match confidence, candidate suggestions for unmatched fields, and a
diagnostics summary.

Semantic-lineage query parameters:

- `semantic_model_id` is required.
- `semantic_model_workspace_id` is optional and defaults to the report
  workspace.
- `reportFormat` accepts `PBIR` or `PBIR-Legacy` and defaults to `PBIR`.
- `semanticModelFormat` accepts `TMDL` or `TMSL` and defaults to `TMDL`.

Do not pass `reportFormat=TMDL`; `TMDL` is only valid for semantic model
definitions.

### XMLA Metadata

```text
GET /api/v1/workspaces/{workspace_id}/semantic-models/{semantic_model_id}/xmla/metadata
```

Optional query parameters:

- `workspaceName`
- `databaseName`

This endpoint uses the Power BI token dependency and the XMLA ADOMD adapter to
query `$SYSTEM.TMSCHEMA_*` rowsets for tables, columns, measures, partitions,
hierarchies, levels, and relationships. Workspace names are URI encoded in the
`powerbi://api.powerbi.com/v1.0/{tenant}/{workspace}` endpoint.

If `pythonnet` or the Microsoft Analysis Services ADOMD assembly is not
available on the host, the client returns `PROVIDER_INTEGRATION_NOT_CONFIGURED`
with a setup message.

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
    report definition, semantic model definition, semantic lineage, and XMLA
    metadata endpoints.
- `app/api/dependencies/credentials.py`
  - FastAPI dependencies for extracting Power BI and Fabric access tokens from
    the auth session cookie.

### `app/clients`

Provider clients. These files should know provider URL/protocol details but
should not contain business normalization logic.

- `provider_http_client.py`
  - Shared HTTP behavior, provider error mapping, and upstream error-detail
    extraction.
- `powerbi_client.py`
  - Power BI REST API client.
- `fabric_client.py`
  - Microsoft Fabric API client.
  - Handles report and semantic model definition endpoints and long-running
    operation result APIs.
  - Uses `PBIR` by default for report definitions and `TMDL` by default for
    semantic model definitions.
- `xmla_client.py`
  - XMLA endpoint and connection-string construction.
  - ADOMD connection wrapper using the ADOMD `AccessToken` property.
  - TMSCHEMA rowset queries and raw metadata mapping for tables, columns,
    measures, partitions, hierarchies, levels, and relationships.
  - Raises a configured integration error when `pythonnet` or the ADOMD client
    assembly is unavailable.
- `snowflake_client.py`
  - Placeholder for future Snowflake integration.

### `app/core`

Cross-cutting application infrastructure.

- `config.py`
  - Environment-backed settings.
  - Includes XMLA tenant, ADOMD DLL path, and access-token expiry settings.
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
- `parsed_semantic_model.py`
  - Parsed TMDL semantic model response with tables, columns, measures,
    relationships, hierarchies, warnings, and source-path evidence.
- `normalized_report_definition.py`
  - API shape for normalized PBIR reports, pages, visuals, positions, semantic
    model references, and visual field references.
- `report_semantic_lineage.py`
  - API shape for report visual field to semantic model object lineage,
    diagnostics, match confidence, and candidate suggestions.
- `xmla_metadata.py`
  - API shape for XMLA semantic model metadata, including tables, columns,
    measures, partitions, hierarchies, relationships, counts, and warnings.
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
  - Defaults report definition extraction to `PBIR`.
  - Preserves Fabric operation failure details when available.
- `semantic_model_definition_service.py`
  - Retrieves Fabric semantic model definitions and handles long-running
    operations.
  - Defaults semantic model definition extraction to `TMDL`.
  - Preserves Fabric operation failure details when available.
- `semantic_model_definition_parser.py`
  - Parses TMDL semantic model definition parts into API-ready semantic objects.
- `report_semantic_lineage_service.py`
  - Matches normalized report visual field references to parsed semantic model
    objects and produces diagnostics.
- `xmla_metadata_service.py`
  - Maps XMLA adapter output into the XMLA metadata response contract and
    validates adapter payload shape.
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
- `tests/unit/test_fabric_client.py`
  - Fabric report and semantic model definition URL/query construction.
- `tests/unit/test_provider_http_client.py`
  - Provider HTTP error mapping and upstream diagnostic detail extraction.
- `tests/unit/test_semantic_model_definition_parser.py`
  - Parsed TMDL semantic model behavior.
- `tests/unit/test_report_semantic_lineage_service.py`
  - Report visual field to semantic model object matching and diagnostics.
- `tests/unit/test_xmla_client.py`
  - XMLA endpoint encoding, connection-string construction, ADOMD rowset
    mapping, adapter setup failures, and access-token redaction.
- `tests/unit/test_xmla_metadata_service.py`
  - XMLA metadata contract mapping and validation.
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
| Aug 28, 2026 | Phase 3.8 | Completed locally | Added parsed semantic model definition output. |
| Aug 28, 2026 | Phase 3.9 | Completed locally | Added report visual field to semantic model object matching. |
| Aug 28, 2026 | Phase 3.10 | Completed locally | Improved TMDL parser fidelity and source-path evidence. |
| Aug 28, 2026 | Phase 3.11 | Completed locally | Added lineage diagnostics, candidate suggestions, and summary counts. |
| Aug 28, 2026 | Phase 3.12 | Completed locally | Added XMLA metadata contracts and service/client boundary. |
| Aug 28, 2026 | Phase 3.12.1 | Completed locally | Corrected Fabric report definition formats to default to PBIR and reject semantic-model-only formats. |
| Aug 28, 2026 | Phase 3.12.2 | Completed locally | Added upstream provider diagnostic detail for Fabric request and operation failures. |
| Aug 28, 2026 | Phase 3.13 | Completed locally | Implemented the XMLA ADOMD adapter path and TMSCHEMA metadata extraction mapping. |

### Latest Completed Phase

Phase 3.13 is the latest completed local phase. It implements the XMLA ADOMD
adapter path behind `XmlaClient`, builds encoded Power BI XMLA workspace
endpoints, uses an ADOMD access token, queries TMSCHEMA rowsets, maps raw XMLA
metadata into the existing metadata contract, and redacts access tokens from
XMLA failure details.

### Next Phase

Phase 3.14 - Live XMLA validation and semantic metadata merge is the next
phase.

Recommended Phase 3.14 work:

- Validate XMLA extraction against a Premium, PPU, or Fabric capacity with XMLA
  enabled.
- Confirm workspace naming, tenant naming, and semantic model `Initial Catalog`
  behavior with real workspaces.
- Decide how XMLA metadata should merge with Fabric TMDL parsing in lineage
  responses.

## Current Review Notes

Phase 3.6 through Phase 3.13 are locally verified with Ruff and pytest. The
only current test-suite warning is a third-party FastAPI/TestClient warning
about Starlette's `httpx` integration.

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
