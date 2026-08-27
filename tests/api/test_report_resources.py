import pytest

from app.api.dependencies.credentials import (
    get_fabric_access_token,
    get_powerbi_access_token,
)
from app.main import app
from app.schemas.report import Report
from app.schemas.report_page import (
    ReportPage,
    ReportPageListResponse,
)
from app.schemas.report_semantic_lineage import (
    ReportSemanticLineageResponse,
    SemanticLineageDiagnosticsSummary,
)
from app.schemas.semantic_model_definition import (
    SemanticModelDefinition,
    SemanticModelDefinitionPart,
    SemanticModelDefinitionResponse,
)
from app.services.report_semantic_lineage_service import (
    ReportSemanticLineageService,
)
from app.services.report_service import (
    ReportService,
)
from app.services.semantic_model_definition_service import (
    SemanticModelDefinitionService,
)

WORKSPACE_ID = (
    "f089354e-8366-4e18-aea3-4cb4a3a50b48"
)

REPORT_ID = (
    "879445d6-3a9e-4a74-b5ae-7c0ddabf0f11"
)

SEMANTIC_MODEL_ID = (
    "cfafbeb1-8037-4d0c-896e-a46fb27ff229"
)


@pytest.fixture(autouse=True)
def override_authentication():
    async def fake_powerbi_token() -> str:
        return "fake-test-token"

    async def fake_fabric_token() -> str:
        return "fake-fabric-token"

    app.dependency_overrides[
        get_powerbi_access_token
    ] = fake_powerbi_token
    app.dependency_overrides[
        get_fabric_access_token
    ] = fake_fabric_token

    yield

    app.dependency_overrides.pop(
        get_powerbi_access_token,
        None,
    )
    app.dependency_overrides.pop(
        get_fabric_access_token,
        None,
    )


def test_get_report(
    client,
    monkeypatch,
):
    async def fake_get_report(
        self,
        *,
        workspace_id: str,
        report_id: str,
        access_token: str,
    ) -> Report:
        return Report(
            id=report_id,
            name="Sales Report",
            dataset_id="dataset-1",
            report_type="PowerBIReport",
            format="PBIR",
        )

    monkeypatch.setattr(
        ReportService,
        "get_report",
        fake_get_report,
    )

    response = client.get(
        
            f"/api/v1/workspaces/"
            f"{WORKSPACE_ID}/reports/"
            f"{REPORT_ID}"
        
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == REPORT_ID
    assert payload["name"] == "Sales Report"
    assert payload["format"] == "PBIR"


def test_list_report_pages(
    client,
    monkeypatch,
):
    async def fake_list_pages(
        self,
        *,
        workspace_id: str,
        report_id: str,
        access_token: str,
    ) -> ReportPageListResponse:
        return ReportPageListResponse(
            workspace_id=workspace_id,
            report_id=report_id,
            pages=[
                ReportPage(
                    name="ReportSection",
                    display_name=(
                        "Executive Summary"
                    ),
                    order=0,
                )
            ],
            count=1,
        )

    monkeypatch.setattr(
        ReportService,
        "list_pages",
        fake_list_pages,
    )

    response = client.get(
        
            f"/api/v1/workspaces/"
            f"{WORKSPACE_ID}/reports/"
            f"{REPORT_ID}/pages"
        
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 1

    assert (
        payload["pages"][0]["name"]
        == "ReportSection"
    )


def test_get_report_page(
    client,
    monkeypatch,
):
    async def fake_get_page(
        self,
        *,
        workspace_id: str,
        report_id: str,
        page_name: str,
        access_token: str,
    ) -> ReportPage:
        return ReportPage(
            name=page_name,
            display_name="Executive Summary",
            order=0,
        )

    monkeypatch.setattr(
        ReportService,
        "get_page",
        fake_get_page,
    )

    response = client.get(
        
            f"/api/v1/workspaces/"
            f"{WORKSPACE_ID}/reports/"
            f"{REPORT_ID}/pages/"
            f"ReportSection"
        
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["name"]
        == "ReportSection"
    )

    assert (
        payload["display_name"]
        == "Executive Summary"
    )


def test_invalid_report_uuid(
    client,
):
    response = client.get(
        
            f"/api/v1/workspaces/"
            f"{WORKSPACE_ID}/reports/"
            f"invalid-report-id"
        
    )

    assert response.status_code == 422


def test_get_semantic_model_definition(
    client,
    monkeypatch,
):
    async def fake_get_definition(
        self,
        *,
        workspace_id: str,
        semantic_model_id: str,
        access_token: str,
        definition_format: str,
    ) -> SemanticModelDefinitionResponse:
        assert workspace_id == WORKSPACE_ID
        assert semantic_model_id == SEMANTIC_MODEL_ID
        assert access_token == "fake-fabric-token"
        assert definition_format == "TMSL"

        return SemanticModelDefinitionResponse(
            workspace_id=workspace_id,
            semantic_model_id=semantic_model_id,
            definition=SemanticModelDefinition(
                format=definition_format,
                parts=[
                    SemanticModelDefinitionPart(
                        path=(
                            "definition/model.tmdl"
                        ),
                        payload=(
                            "bW9kZWwgTW9kZWw="
                        ),
                        payload_type=(
                            "InlineBase64"
                        ),
                    )
                ],
            ),
        )

    monkeypatch.setattr(
        SemanticModelDefinitionService,
        "get_definition",
        fake_get_definition,
    )

    response = client.post(
        f"/api/v1/workspaces/{WORKSPACE_ID}/"
        "semantic-models/"
        f"{SEMANTIC_MODEL_ID}/definition"
        "?format=TMSL"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["workspace_id"] == WORKSPACE_ID
    assert (
        payload["semantic_model_id"]
        == SEMANTIC_MODEL_ID
    )
    assert (
        payload["definition"]["format"]
        == "TMSL"
    )
    assert (
        payload["definition"]["parts"][0][
            "payloadType"
        ]
        == "InlineBase64"
    )
    assert (
        "payload_type"
        not in payload["definition"]["parts"][0]
    )


def test_semantic_model_definition_rejects_invalid_format(
    client,
):
    response = client.post(
        f"/api/v1/workspaces/{WORKSPACE_ID}/"
        "semantic-models/"
        f"{SEMANTIC_MODEL_ID}/definition"
        "?format=PBIR"
    )

    assert response.status_code == 422


def test_get_report_semantic_lineage(
    client,
    monkeypatch,
):
    expected_semantic_model_workspace_id = (
        "a2f8996f-8f1a-46e3-8f7c-3f2d2145df45"
    )

    async def fake_build_lineage(
        self,
        *,
        workspace_id: str,
        report_id: str,
        semantic_model_workspace_id: str,
        semantic_model_id: str,
        access_token: str,
        report_definition_format: str | None,
        semantic_model_definition_format: str,
    ) -> ReportSemanticLineageResponse:
        assert workspace_id == WORKSPACE_ID
        assert report_id == REPORT_ID
        assert (
            semantic_model_workspace_id
            == expected_semantic_model_workspace_id
        )
        assert semantic_model_id == SEMANTIC_MODEL_ID
        assert access_token == "fake-fabric-token"
        assert report_definition_format == "PBIR"
        assert (
            semantic_model_definition_format
            == "TMDL"
        )

        return ReportSemanticLineageResponse(
            workspace_id=workspace_id,
            report_id=report_id,
            semantic_model_workspace_id=(
                semantic_model_workspace_id
            ),
            semantic_model_id=semantic_model_id,
            total_field_reference_count=1,
            matched_field_reference_count=1,
            unmatched_field_reference_count=0,
            diagnostics_summary=(
                SemanticLineageDiagnosticsSummary(
                    status_counts={
                        "matched": 1,
                        "unmatched": 0,
                    }
                )
            ),
        )

    monkeypatch.setattr(
        ReportSemanticLineageService,
        "build_lineage",
        fake_build_lineage,
    )

    response = client.post(
        f"/api/v1/workspaces/{WORKSPACE_ID}/"
        f"reports/{REPORT_ID}/semantic-lineage"
        f"?semantic_model_id={SEMANTIC_MODEL_ID}"
        "&reportFormat=PBIR"
        "&semanticModelFormat=TMDL"
        "&semantic_model_workspace_id="
        f"{expected_semantic_model_workspace_id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["workspace_id"] == WORKSPACE_ID
    assert payload["report_id"] == REPORT_ID
    assert (
        payload["semantic_model_workspace_id"]
        == expected_semantic_model_workspace_id
    )
    assert (
        payload["semantic_model_id"]
        == SEMANTIC_MODEL_ID
    )
    assert (
        payload["matched_field_reference_count"]
        == 1
    )
    assert (
        payload["diagnostics_summary"][
            "status_counts"
        ]
        == {
            "matched": 1,
            "unmatched": 0,
        }
    )
