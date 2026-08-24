from typing import Any

from app.clients.powerbi_client import PowerBIClient
from app.core.exceptions import UpstreamInvalidResponseError
from app.schemas.report import (
    Report,
    ReportListResponse,
)


class ReportService:
    def __init__(self) -> None:
        self.client = PowerBIClient()

    async def list_reports(
        self,
        *,
        workspace_id: str,
        access_token: str,
    ) -> ReportListResponse:
        raw_reports = (
            await self.client.get_reports_in_workspace(
                workspace_id=workspace_id,
                access_token=access_token,
            )
        )

        reports = [
            self._map_report(report)
            for report in raw_reports
        ]

        return ReportListResponse(
            workspace_id=workspace_id,
            reports=reports,
            count=len(reports),
        )

    @staticmethod
    def _map_report(
        report: dict[str, Any],
    ) -> Report:
        report_id = report.get("id")
        report_name = report.get("name")

        if (
            not isinstance(report_id, str)
            or not report_id
        ):
            raise UpstreamInvalidResponseError(
                "powerbi"
            )

        if (
            not isinstance(report_name, str)
            or not report_name
        ):
            raise UpstreamInvalidResponseError(
                "powerbi"
            )

        return Report(
            id=report_id,
            name=report_name,
            dataset_id=report.get(
                "datasetId"
            ),
            report_type=report.get(
                "reportType"
            ),
            format=report.get(
                "format"
            ),
            web_url=report.get(
                "webUrl"
            ),
            is_owned_by_me=report.get(
                "isOwnedByMe"
            ),
        )