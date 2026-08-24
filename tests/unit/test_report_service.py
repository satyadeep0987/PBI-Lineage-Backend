from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import UpstreamInvalidResponseError
from app.services.report_service import ReportService


@pytest.mark.asyncio
async def test_list_reports_maps_powerbi_response():
    service = ReportService()

    service.client.get_reports_in_workspace = AsyncMock(
        return_value=[
            {
                "id": "report-1",
                "name": "Sales Analysis",
                "datasetId": "dataset-1",
                "reportType": "PowerBIReport",
                "format": "PBIR",
                "webUrl": "https://app.powerbi.com/report-1",
                "isOwnedByMe": True,
            }
        ]
    )

    result = await service.list_reports(
        workspace_id="workspace-1",
        access_token="fake-token",
    )

    assert result.workspace_id == "workspace-1"
    assert result.count == 1

    report = result.reports[0]

    assert report.id == "report-1"
    assert report.name == "Sales Analysis"
    assert report.dataset_id == "dataset-1"
    assert report.report_type == "PowerBIReport"
    assert report.format == "PBIR"
    assert report.web_url == "https://app.powerbi.com/report-1"
    assert report.is_owned_by_me is True


@pytest.mark.asyncio
async def test_list_reports_allows_missing_dataset_id():
    service = ReportService()

    service.client.get_reports_in_workspace = AsyncMock(
        return_value=[
            {
                "id": "report-1",
                "name": "Paginated Report",
                "reportType": "PaginatedReport",
            }
        ]
    )

    result = await service.list_reports(
        workspace_id="workspace-1",
        access_token="fake-token",
    )

    assert result.count == 1

    report = result.reports[0]

    assert report.id == "report-1"
    assert report.name == "Paginated Report"
    assert report.dataset_id is None


@pytest.mark.asyncio
async def test_list_reports_handles_empty_workspace():
    service = ReportService()

    service.client.get_reports_in_workspace = AsyncMock(
        return_value=[]
    )

    result = await service.list_reports(
        workspace_id="workspace-1",
        access_token="fake-token",
    )

    assert result.workspace_id == "workspace-1"
    assert result.count == 0
    assert result.reports == []


@pytest.mark.asyncio
async def test_report_missing_id_raises_invalid_response():
    service = ReportService()

    service.client.get_reports_in_workspace = AsyncMock(
        return_value=[
            {
                "name": "Sales Analysis",
                "datasetId": "dataset-1",
            }
        ]
    )

    with pytest.raises(
        UpstreamInvalidResponseError
    ):
        await service.list_reports(
            workspace_id="workspace-1",
            access_token="fake-token",
        )


@pytest.mark.asyncio
async def test_report_missing_name_raises_invalid_response():
    service = ReportService()

    service.client.get_reports_in_workspace = AsyncMock(
        return_value=[
            {
                "id": "report-1",
                "datasetId": "dataset-1",
            }
        ]
    )

    with pytest.raises(
        UpstreamInvalidResponseError
    ):
        await service.list_reports(
            workspace_id="workspace-1",
            access_token="fake-token",
        )


@pytest.mark.asyncio
async def test_report_empty_id_raises_invalid_response():
    service = ReportService()

    service.client.get_reports_in_workspace = AsyncMock(
        return_value=[
            {
                "id": "",
                "name": "Sales Analysis",
            }
        ]
    )

    with pytest.raises(
        UpstreamInvalidResponseError
    ):
        await service.list_reports(
            workspace_id="workspace-1",
            access_token="fake-token",
        )


@pytest.mark.asyncio
async def test_report_empty_name_raises_invalid_response():
    service = ReportService()

    service.client.get_reports_in_workspace = AsyncMock(
        return_value=[
            {
                "id": "report-1",
                "name": "",
            }
        ]
    )

    with pytest.raises(
        UpstreamInvalidResponseError
    ):
        await service.list_reports(
            workspace_id="workspace-1",
            access_token="fake-token",
        )