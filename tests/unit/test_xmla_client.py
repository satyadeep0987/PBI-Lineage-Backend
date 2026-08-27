import pytest

from app.clients.xmla_client import XmlaClient
from app.core.exceptions import (
    ProviderIntegrationNotConfiguredError,
)


def test_build_workspace_endpoint_uses_workspace_name():
    endpoint = XmlaClient().build_workspace_endpoint(
        workspace_id="workspace-123",
        workspace_name="Sales Workspace",
    )

    assert endpoint == (
        "powerbi://api.powerbi.com/v1.0/"
        "myorg/Sales Workspace"
    )


def test_build_workspace_endpoint_falls_back_to_workspace_id():
    endpoint = XmlaClient().build_workspace_endpoint(
        workspace_id="workspace-123",
    )

    assert endpoint == (
        "powerbi://api.powerbi.com/v1.0/"
        "myorg/workspace-123"
    )


@pytest.mark.asyncio
async def test_xmla_metadata_boundary_is_not_configured():
    client = XmlaClient()

    with pytest.raises(
        ProviderIntegrationNotConfiguredError
    ) as exc_info:
        await client.get_semantic_model_metadata(
            workspace_id="workspace-123",
            semantic_model_id="model-123",
            access_token="token",
            workspace_name="Sales Workspace",
            database_name="Sales Model",
        )

    assert exc_info.value.provider == "xmla"
    assert exc_info.value.code == (
        "PROVIDER_INTEGRATION_NOT_CONFIGURED"
    )
    assert (
        "Configure a live XMLA transport adapter"
        in exc_info.value.message
    )
