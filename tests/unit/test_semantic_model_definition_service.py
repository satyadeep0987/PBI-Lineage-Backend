from unittest.mock import AsyncMock

import httpx
import pytest

from app.services.semantic_model_definition_service import (
    SemanticModelDefinitionService,
)


@pytest.mark.asyncio
async def test_get_semantic_model_definition():
    service = (
        SemanticModelDefinitionService()
    )

    service.client = AsyncMock()

    response = httpx.Response(
        status_code=200,
        json={
            "definition": {
                "format": "TMDL",
                "parts": [
                    {
                        "path": (
                            "definition/model.tmdl"
                        ),
                        "payload": (
                            "bW9kZWwgTW9kZWw="
                        ),
                        "payloadType": (
                            "InlineBase64"
                        ),
                    },
                    {
                        "path": (
                            "definition/tables/"
                            "Sales.tmdl"
                        ),
                        "payload": (
                            "dGFibGUgU2FsZXM="
                        ),
                        "payloadType": (
                            "InlineBase64"
                        ),
                    },
                ],
            }
        },
    )

    service.client.start_semantic_model_definition.return_value = (
        response
    )

    result = await service.get_definition(
        workspace_id="workspace-123",
        semantic_model_id="model-123",
        access_token="token",
        definition_format="TMDL",
    )

    assert (
        result.workspace_id
        == "workspace-123"
    )

    assert (
        result.semantic_model_id
        == "model-123"
    )

    assert (
        result.definition.format
        == "TMDL"
    )

    assert len(
        result.definition.parts
    ) == 2

    assert (
        result.definition.parts[0].path
        == "definition/model.tmdl"
    )

    assert (
        result.definition.parts[0].payload
        == "bW9kZWwgTW9kZWw="
    )

    assert (
        result.definition.parts[0].payload_type
        == "InlineBase64"
    )

    assert (
        result.definition.parts[1].path
        == (
            "definition/tables/"
            "Sales.tmdl"
        )
    )

    service.client.start_semantic_model_definition.assert_awaited_once_with(
        workspace_id="workspace-123",
        semantic_model_id="model-123",
        access_token="token",
        definition_format="TMDL",
    )