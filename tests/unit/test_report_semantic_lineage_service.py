from unittest.mock import AsyncMock

import pytest

from app.schemas.normalized_report_definition import (
    NormalizedReportDefinitionResponse,
    NormalizedReportPage,
    NormalizedReportVisual,
    VisualFieldReference,
)
from app.schemas.parsed_semantic_model import (
    ParsedSemanticModelColumn,
    ParsedSemanticModelHierarchy,
    ParsedSemanticModelHierarchyLevel,
    ParsedSemanticModelMeasure,
    ParsedSemanticModelResponse,
    ParsedSemanticModelTable,
    ParsedSemanticModelWarning,
)
from app.services.report_semantic_lineage_service import (
    ReportSemanticLineageService,
)


def _normalized_report() -> NormalizedReportDefinitionResponse:
    return NormalizedReportDefinitionResponse(
        workspace_id="report-workspace",
        report_id="report-123",
        format="PBIR",
        pages=[
            NormalizedReportPage(
                name="ReportSection",
                display_name="Overview",
                visuals=[
                    NormalizedReportVisual(
                        id="visual-1",
                        internal_name="visual-1",
                        title="Sales Overview",
                        visual_type="barChart",
                        has_query=True,
                        field_references=[
                            VisualFieldReference(
                                object_type="column",
                                table_name="Product",
                                object_name="Category",
                                usage="projection",
                                role="Axis",
                            ),
                            VisualFieldReference(
                                object_type="measure",
                                table_name="Sales",
                                object_name="Total Sales",
                                usage="projection",
                                role="Values",
                            ),
                            VisualFieldReference(
                                object_type=(
                                    "hierarchy_level"
                                ),
                                table_name="Date",
                                object_name="Year",
                                hierarchy_name="Calendar",
                                level_name="Year",
                                usage="projection",
                                role="Axis",
                            ),
                            VisualFieldReference(
                                object_type="column",
                                table_name="Sales",
                                object_name="Missing Column",
                                usage="filter",
                            ),
                        ],
                    )
                ],
                visual_count=1,
            )
        ],
        page_count=1,
        visual_count=1,
        source_part_count=1,
        decoded_json_part_count=1,
        warnings=[
            "Report warning."
        ],
    )


def _parsed_semantic_model() -> ParsedSemanticModelResponse:
    return ParsedSemanticModelResponse(
        workspace_id="model-workspace",
        semantic_model_id="model-123",
        format="TMDL",
        tables=[
            ParsedSemanticModelTable(
                name="Product",
                source_path=(
                    "definition/tables/Product.tmdl"
                ),
                columns=[
                    ParsedSemanticModelColumn(
                        name="Category",
                        source_path=(
                            "definition/tables/Product.tmdl"
                        ),
                    )
                ],
            ),
            ParsedSemanticModelTable(
                name="Sales",
                source_path=(
                    "definition/tables/Sales.tmdl"
                ),
                measures=[
                    ParsedSemanticModelMeasure(
                        name="Total Sales",
                        source_path=(
                            "definition/tables/Sales.tmdl"
                        ),
                        expression=(
                            "SUM(Sales[Amount])"
                        ),
                    )
                ],
            ),
            ParsedSemanticModelTable(
                name="Date",
                source_path=(
                    "definition/tables/Date.tmdl"
                ),
                hierarchies=[
                    ParsedSemanticModelHierarchy(
                        name="Calendar",
                        source_path=(
                            "definition/tables/Date.tmdl"
                        ),
                        levels=[
                            ParsedSemanticModelHierarchyLevel(
                                name="Year",
                                source_path=(
                                    "definition/tables/Date.tmdl"
                                ),
                                column="Year",
                            )
                        ],
                    )
                ],
            ),
        ],
        warnings=[
            ParsedSemanticModelWarning(
                code="MODEL_WARNING",
                message="Semantic warning.",
                path="definition/model.tmdl",
            )
        ],
    )


def test_match_report_fields_to_semantic_model_objects():
    service = ReportSemanticLineageService()

    result = service.match(
        report=_normalized_report(),
        semantic_model=(
            _parsed_semantic_model()
        ),
        semantic_model_workspace_id=(
            "model-workspace"
        ),
    )

    assert (
        result.workspace_id
        == "report-workspace"
    )
    assert (
        result.semantic_model_workspace_id
        == "model-workspace"
    )
    assert (
        result.semantic_model_id
        == "model-123"
    )
    assert (
        result.total_field_reference_count
        == 4
    )
    assert (
        result.matched_field_reference_count
        == 3
    )
    assert (
        result.unmatched_field_reference_count
        == 1
    )

    matched_objects = [
        field_match.semantic_object
        for field_match in result.field_matches
        if field_match.status == "matched"
    ]

    assert [
        item.object_type
        for item in matched_objects
        if item is not None
    ] == [
        "column",
        "measure",
        "hierarchy_level",
    ]
    assert [
        item.source_path
        for item in matched_objects
        if item is not None
    ] == [
        "definition/tables/Product.tmdl",
        "definition/tables/Sales.tmdl",
        "definition/tables/Date.tmdl",
    ]

    unmatched = [
        field_match
        for field_match in result.field_matches
        if field_match.status == "unmatched"
    ]

    assert len(unmatched) == 1
    assert (
        unmatched[0].reason
        == "object_not_found"
    )
    assert result.warnings == [
        "Report warning.",
        (
            "MODEL_WARNING: Semantic warning. "
            "(definition/model.tmdl)"
        ),
    ]


@pytest.mark.asyncio
async def test_build_lineage_uses_report_and_semantic_model_services():
    service = ReportSemanticLineageService()

    service.report_definition_service = AsyncMock()
    (
        service.report_definition_service
        .get_normalized_definition
        .return_value
    ) = _normalized_report()

    service.semantic_model_definition_service = (
        AsyncMock()
    )
    (
        service.semantic_model_definition_service
        .get_parsed_definition
        .return_value
    ) = _parsed_semantic_model()

    result = await service.build_lineage(
        workspace_id="report-workspace",
        report_id="report-123",
        semantic_model_workspace_id=(
            "model-workspace"
        ),
        semantic_model_id="model-123",
        access_token="fabric-token",
        report_definition_format="PBIR",
        semantic_model_definition_format="TMDL",
    )

    assert (
        result.matched_field_reference_count
        == 3
    )

    (
        service.report_definition_service
        .get_normalized_definition
        .assert_awaited_once_with(
            workspace_id="report-workspace",
            report_id="report-123",
            access_token="fabric-token",
            definition_format="PBIR",
        )
    )
    (
        service.semantic_model_definition_service
        .get_parsed_definition
        .assert_awaited_once_with(
            workspace_id="model-workspace",
            semantic_model_id="model-123",
            access_token="fabric-token",
            definition_format="TMDL",
        )
    )
