from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from app.api.dependencies.credentials import (
    get_powerbi_access_token,
)
from app.schemas.report import (
    ReportListResponse,
)
from app.schemas.semantic_model import (
    SemanticModelListResponse,
)
from app.schemas.workspace import (
    Workspace,
    WorkspaceListResponse,
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