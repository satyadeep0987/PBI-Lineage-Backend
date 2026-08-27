import base64

from app.schemas.semantic_model_definition import (
    SemanticModelDefinition,
    SemanticModelDefinitionPart,
    SemanticModelDefinitionResponse,
)
from app.services.semantic_model_definition_parser import (
    SemanticModelDefinitionParser,
)


def _encode(
    text: str,
) -> str:
    return (
        base64.b64encode(
            text.encode("utf-8")
        )
        .decode("ascii")
    )


def _raw_definition(
    *,
    text: str,
    definition_format: str = "TMDL",
    payload_type: str = "InlineBase64",
) -> SemanticModelDefinitionResponse:
    return SemanticModelDefinitionResponse(
        workspace_id="workspace-123",
        semantic_model_id="model-123",
        definition=SemanticModelDefinition(
            format=definition_format,
            parts=[
                SemanticModelDefinitionPart(
                    path="definition/tables/Sales.tmdl",
                    payload=_encode(text),
                    payload_type=payload_type,
                )
            ],
        ),
    )


def test_parse_tmdl_table():
    raw = _raw_definition(
        text="""
table Sales
"""
    )

    result = SemanticModelDefinitionParser().parse(
        raw
    )

    assert result.workspace_id == "workspace-123"
    assert result.semantic_model_id == "model-123"
    assert result.format == "TMDL"
    assert len(result.tables) == 1
    assert result.tables[0].name == "Sales"


def test_parse_tmdl_column():
    raw = _raw_definition(
        text="""
table Sales
    column Amount
        dataType: decimal
        sourceColumn: Amount
        isHidden: false
"""
    )

    result = SemanticModelDefinitionParser().parse(
        raw
    )

    column = result.tables[0].columns[0]

    assert column.name == "Amount"
    assert column.data_type == "decimal"
    assert column.source_column == "Amount"
    assert column.is_hidden is False


def test_parse_tmdl_measure():
    raw = _raw_definition(
        text="""
table Sales
    measure Total Sales = SUM(Sales[Amount])
        formatString: '$#,0.00'
        isHidden: false
"""
    )

    result = SemanticModelDefinitionParser().parse(
        raw
    )

    measure = result.tables[0].measures[0]

    assert measure.name == "Total Sales"
    assert measure.expression == "SUM(Sales[Amount])"
    assert measure.format_string == "$#,0.00"
    assert measure.is_hidden is False


def test_parse_tmdl_relationship():
    raw = _raw_definition(
        text="""
relationship SalesCustomer
    fromColumn: Sales[CustomerId]
    toColumn: Customer[CustomerId]
    isActive: true
    cardinality: manyToOne
    crossFilteringBehavior: bothDirections
"""
    )

    result = SemanticModelDefinitionParser().parse(
        raw
    )

    relationship = result.relationships[0]

    assert relationship.name == "SalesCustomer"
    assert relationship.from_table == "Sales"
    assert relationship.from_column == "CustomerId"
    assert relationship.to_table == "Customer"
    assert relationship.to_column == "CustomerId"
    assert relationship.is_active is True
    assert relationship.cardinality == "manyToOne"
    assert (
        relationship.cross_filter_direction
        == "bothDirections"
    )


def test_invalid_base64_adds_warning():
    raw = SemanticModelDefinitionResponse(
        workspace_id="workspace-123",
        semantic_model_id="model-123",
        definition=SemanticModelDefinition(
            format="TMDL",
            parts=[
                SemanticModelDefinitionPart(
                    path="definition/tables/Sales.tmdl",
                    payload="not-valid-base64",
                    payload_type="InlineBase64",
                )
            ],
        ),
    )

    result = SemanticModelDefinitionParser().parse(
        raw
    )

    assert result.tables == []
    assert len(result.warnings) == 1
    assert (
        result.warnings[0].code
        == "INVALID_BASE64_PAYLOAD"
    )
    assert (
        result.warnings[0].path
        == "definition/tables/Sales.tmdl"
    )


def test_tmsl_returns_unsupported_warning():
    raw = _raw_definition(
        text="{}",
        definition_format="TMSL",
    )

    result = SemanticModelDefinitionParser().parse(
        raw
    )

    assert result.tables == []
    assert len(result.warnings) == 1
    assert (
        result.warnings[0].code
        == "UNSUPPORTED_FORMAT"
    )