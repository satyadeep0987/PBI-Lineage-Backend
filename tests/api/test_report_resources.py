import pytest

from app.api.dependencies.credentials import (
    get_powerbi_access_token,
)
from app.main import app
from app.schemas.report import Report
from app.schemas.report_page import (
    ReportPage,
    ReportPageListResponse,
)
from app.services.report_service import (
    ReportService,
)

WORKSPACE_ID = (
    "f089354e-8366-4e18-aea3-4cb4a3a50b48"
)

REPORT_ID = (
    "879445d6-3a9e-4a74-b5ae-7c0ddabf0f11"
)


@pytest.fixture(autouse=True)
def override_authentication():
    async def fake_powerbi_token() -> str:
        return "fake-test-token"

    app.dependency_overrides[
        get_powerbi_access_token
    ] = fake_powerbi_token

    yield

    app.dependency_overrides.pop(
        get_powerbi_access_token,
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