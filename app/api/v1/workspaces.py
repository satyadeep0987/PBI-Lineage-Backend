from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from app.api.dependencies.credentials import (
    get_powerbi_access_token,
)
from app.schemas.workspace import (
    WorkspaceListResponse,
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
        Depends(get_powerbi_access_token),
    ],
    top: Annotated[
        int,
        Query(
            ge=1,
            le=500,
            description=(
                "Maximum number of workspaces "
                "to return."
            ),
        ),
    ] = 100,
    skip: Annotated[
        int,
        Query(
            ge=0,
            description=(
                "Number of workspaces to skip."
            ),
        ),
    ] = 0,
) -> WorkspaceListResponse:
    service = WorkspaceService()

    return await service.list_workspaces(
        access_token=access_token,
        top=top,
        skip=skip,
    )