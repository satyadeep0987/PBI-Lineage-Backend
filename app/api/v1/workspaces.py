from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
)

from app.api.dependencies.credentials import (
    get_fabric_access_token,
    get_powerbi_access_token,
)
from app.schemas.normalized_report_definition import (
    NormalizedReportDefinitionResponse,
)
from app.schemas.report import (
    Report,
    ReportListResponse,
)
from app.schemas.report_definition import (
    ReportDefinitionResponse,
)
from app.schemas.report_page import (
    ReportPage,
    ReportPageListResponse,
)
from app.schemas.semantic_model import (
    SemanticModelListResponse,
)
from app.schemas.workspace import (
    Workspace,
    WorkspaceListResponse,
)
from app.services.report_definition_service import (
    ReportDefinitionService,
)
from app.services.report_service import (
    ReportService,
)
from app.services.semantic_model_service import (
    SemanticModelService,
)
from app.services.workspace_service import (
    WorkspaceService,
)

router = APIRouter()


@router.get(
    "",
    response_model=WorkspaceListResponse,
)
async def list_workspaces(
    access_token: Annotated[
        str,
        Depends(
            get_powerbi_access_token
        ),
    ],
    top: Annotated[
        int,
        Query(
            ge=1,
            le=500,
        ),
    ] = 100,
    skip: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
) -> WorkspaceListResponse:
    service = WorkspaceService()

    return await service.list_workspaces(
        access_token=access_token,
        top=top,
        skip=skip,
    )


@router.get(
    "/{workspace_id}",
    response_model=Workspace,
)
async def get_workspace(
    workspace_id: UUID,
    access_token: Annotated[
        str,
        Depends(
            get_powerbi_access_token
        ),
    ],
) -> Workspace:
    service = WorkspaceService()

    return await service.get_workspace(
        workspace_id=str(workspace_id),
        access_token=access_token,
    )


@router.get(
    "/{workspace_id}/reports",
    response_model=ReportListResponse,
)
async def list_workspace_reports(
    workspace_id: UUID,
    access_token: Annotated[
        str,
        Depends(
            get_powerbi_access_token
        ),
    ],
) -> ReportListResponse:
    service = ReportService()

    return await service.list_reports(
        workspace_id=str(workspace_id),
        access_token=access_token,
    )


@router.get(
    "/{workspace_id}/semantic-models",
    response_model=SemanticModelListResponse,
)
async def list_workspace_semantic_models(
    workspace_id: UUID,
    access_token: Annotated[
        str,
        Depends(
            get_powerbi_access_token
        ),
    ],
) -> SemanticModelListResponse:
    service = SemanticModelService()

    return await service.list_semantic_models(
        workspace_id=str(workspace_id),
        access_token=access_token,
    )

@router.get(
    "/{workspace_id}/reports/{report_id}",
    response_model=Report,
)
async def get_workspace_report(
    workspace_id: UUID,
    report_id: UUID,
    access_token: Annotated[
        str,
        Depends(
            get_powerbi_access_token
        ),
    ],
) -> Report:
    service = ReportService()

    return await service.get_report(
        workspace_id=str(workspace_id),
        report_id=str(report_id),
        access_token=access_token,
    )

@router.get(
    "/{workspace_id}/reports/{report_id}/pages",
    response_model=ReportPageListResponse,
)
async def list_workspace_report_pages(
    workspace_id: UUID,
    report_id: UUID,
    access_token: Annotated[
        str,
        Depends(
            get_powerbi_access_token
        ),
    ],
) -> ReportPageListResponse:
    service = ReportService()

    return await service.list_pages(
        workspace_id=str(workspace_id),
        report_id=str(report_id),
        access_token=access_token,
    )

@router.get(
    (
        "/{workspace_id}/reports/"
        "{report_id}/pages/{page_name}"
    ),
    response_model=ReportPage,
)
async def get_workspace_report_page(
    workspace_id: UUID,
    report_id: UUID,
    page_name: Annotated[
        str,
        Path(
            min_length=1,
            max_length=256,
        ),
    ],
    access_token: Annotated[
        str,
        Depends(
            get_powerbi_access_token
        ),
    ],
) -> ReportPage:
    service = ReportService()

    return await service.get_page(
        workspace_id=str(workspace_id),
        report_id=str(report_id),
        page_name=page_name,
        access_token=access_token,
    )

@router.post(
    (
        "/{workspace_id}/reports/"
        "{report_id}/definition"
    ),
    response_model=(
        ReportDefinitionResponse
    ),
)
async def get_workspace_report_definition(
    workspace_id: UUID,
    report_id: UUID,
    access_token: Annotated[
        str,
        Depends(
            get_fabric_access_token
        ),
    ],
    definition_format: Annotated[
        str | None,
        Query(
            alias="format",
            min_length=1,
            max_length=64,
        ),
    ] = None,
) -> ReportDefinitionResponse:
    service = (
        ReportDefinitionService()
    )

    return await service.get_definition(
        workspace_id=str(
            workspace_id
        ),
        report_id=str(
            report_id
        ),
        access_token=access_token,
        definition_format=(
            definition_format
        ),
    )

@router.post(
    (
        "/{workspace_id}/reports/"
        "{report_id}/definition/normalized"
    ),
    response_model=(
        NormalizedReportDefinitionResponse
    ),
)
async def get_normalized_report_definition(
    workspace_id: UUID,
    report_id: UUID,
    access_token: Annotated[
        str,
        Depends(
            get_fabric_access_token
        ),
    ],
    definition_format: Annotated[
        str | None,
        Query(
            alias="format",
            min_length=1,
            max_length=64,
        ),
    ] = None,
) -> NormalizedReportDefinitionResponse:
    service = (
        ReportDefinitionService()
    )

    return await (
        service.get_normalized_definition(
            workspace_id=str(
                workspace_id
            ),
            report_id=str(
                report_id
            ),
            access_token=access_token,
            definition_format=(
                definition_format
            ),
        )
    )