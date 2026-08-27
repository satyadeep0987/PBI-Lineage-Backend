import pytest

from app.core.exceptions import (
    UpstreamInvalidResponseError,
)
from app.services.xmla_metadata_service import (
    XmlaMetadataService,
)


class _FakeXmlaClient:
    def __init__(
        self,
        payload: dict,
    ) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def build_workspace_endpoint(
        self,
        *,
        workspace_id: str,
        workspace_name: str | None = None,
    ) -> str:
        target = workspace_name or workspace_id

        return (
            "powerbi://api.powerbi.com/v1.0/"
            f"myorg/{target}"
        )

    async def get_semantic_model_metadata(
        self,
        **kwargs,
    ) -> dict:
        self.calls.append(
            kwargs
        )

        return self.payload


def _metadata_payload() -> dict:
    return {
        "databaseName": "Sales Model",
        "tables": [
            {
                "name": "Sales",
                "description": (
                    "Sales fact table"
                ),
                "isHidden": False,
                "columns": [
                    {
                        "name": "Amount",
                        "dataType": "Decimal",
                        "sourceColumn": (
                            "SalesAmount"
                        ),
                        "formatString": "$#,0.00",
                        "summarizeBy": "Sum",
                        "isHidden": False,
                        "lineageTag": (
                            "amount-lineage"
                        ),
                    }
                ],
                "measures": [
                    {
                        "name": "Total Sales",
                        "expression": (
                            "SUM(Sales[Amount])"
                        ),
                        "formatString": "$#,0.00",
                        "isHidden": False,
                    }
                ],
                "partitions": [
                    {
                        "name": "Sales",
                        "mode": "Import",
                        "sourceType": "M",
                        "expression": (
                            "let Source = ..."
                        ),
                        "isRefreshable": True,
                    }
                ],
                "hierarchies": [
                    {
                        "name": "Calendar",
                        "isHidden": False,
                        "levels": [
                            {
                                "name": "Year",
                                "column": "Year",
                                "ordinal": 0,
                            }
                        ],
                    }
                ],
            }
        ],
        "relationships": [
            {
                "name": "Sales_Date",
                "fromTable": "Sales",
                "fromColumn": "DateKey",
                "toTable": "Date",
                "toColumn": "DateKey",
                "isActive": True,
                "cardinality": "ManyToOne",
                "crossFilterDirection": "Single",
                "securityFilteringBehavior": "OneDirection",
            }
        ],
        "warnings": [
            {
                "code": "XMLA_PARTIAL_METADATA",
                "message": (
                    "Some annotations were skipped."
                ),
                "objectName": "Sales",
            }
        ],
    }


@pytest.mark.asyncio
async def test_get_xmla_metadata_maps_client_payload():
    service = XmlaMetadataService()
    fake_client = _FakeXmlaClient(
        _metadata_payload()
    )
    service.client = fake_client

    result = await service.get_metadata(
        workspace_id="workspace-123",
        semantic_model_id="model-123",
        access_token="token",
        workspace_name="Sales Workspace",
        database_name="Sales Model",
    )

    assert result.workspace_id == "workspace-123"
    assert (
        result.semantic_model_id
        == "model-123"
    )
    assert result.source == "xmla"
    assert result.xmla_endpoint == (
        "powerbi://api.powerbi.com/v1.0/"
        "myorg/Sales Workspace"
    )
    assert result.database_name == "Sales Model"
    assert result.table_count == 1
    assert result.column_count == 1
    assert result.measure_count == 1
    assert result.relationship_count == 1
    assert result.hierarchy_count == 1
    assert result.partition_count == 1

    table = result.tables[0]

    assert table.name == "Sales"
    assert (
        table.columns[0].source_column
        == "SalesAmount"
    )
    assert (
        table.measures[0].expression
        == "SUM(Sales[Amount])"
    )
    assert (
        table.partitions[0].source_type
        == "M"
    )
    assert (
        table.hierarchies[0]
        .levels[0]
        .ordinal
        == 0
    )
    assert (
        result.relationships[0]
        .cross_filter_direction
        == "Single"
    )
    assert (
        result.warnings[0].code
        == "XMLA_PARTIAL_METADATA"
    )
    assert fake_client.calls == [
        {
            "workspace_id": "workspace-123",
            "semantic_model_id": "model-123",
            "access_token": "token",
            "workspace_name": "Sales Workspace",
            "database_name": "Sales Model",
        }
    ]


@pytest.mark.asyncio
async def test_get_xmla_metadata_uses_requested_database_name_fallback():
    service = XmlaMetadataService()
    fake_client = _FakeXmlaClient(
        {
            "tables": [],
        }
    )
    service.client = fake_client

    result = await service.get_metadata(
        workspace_id="workspace-123",
        semantic_model_id="model-123",
        access_token="token",
        database_name="Sales Model",
    )

    assert result.database_name == "Sales Model"
    assert result.table_count == 0


@pytest.mark.asyncio
async def test_get_xmla_metadata_rejects_missing_tables():
    service = XmlaMetadataService()
    service.client = _FakeXmlaClient(
        {}
    )

    with pytest.raises(
        UpstreamInvalidResponseError
    ):
        await service.get_metadata(
            workspace_id="workspace-123",
            semantic_model_id="model-123",
            access_token="token",
        )


@pytest.mark.asyncio
async def test_get_xmla_metadata_rejects_invalid_table_name():
    service = XmlaMetadataService()
    service.client = _FakeXmlaClient(
        {
            "tables": [
                {
                    "name": "",
                }
            ],
        }
    )

    with pytest.raises(
        UpstreamInvalidResponseError
    ):
        await service.get_metadata(
            workspace_id="workspace-123",
            semantic_model_id="model-123",
            access_token="token",
        )
