import base64
import binascii
import re

from app.schemas.parsed_semantic_model import (
    ParsedSemanticModelColumn,
    ParsedSemanticModelHierarchy,
    ParsedSemanticModelHierarchyLevel,
    ParsedSemanticModelMeasure,
    ParsedSemanticModelRelationship,
    ParsedSemanticModelResponse,
    ParsedSemanticModelTable,
    ParsedSemanticModelWarning,
)
from app.schemas.semantic_model_definition import SemanticModelDefinitionResponse


class SemanticModelDefinitionParser:
    def parse(
        self,
        raw: SemanticModelDefinitionResponse,
    ) -> ParsedSemanticModelResponse:
        result = ParsedSemanticModelResponse(
            workspace_id=raw.workspace_id,
            semantic_model_id=raw.semantic_model_id,
            format=raw.definition.format,
        )

        if (raw.definition.format or "").upper() != "TMDL":
            result.warnings.append(
                ParsedSemanticModelWarning(
                    code="UNSUPPORTED_FORMAT",
                    message="Only TMDL parsing is supported in this phase.",
                )
            )
            return result

        for part in raw.definition.parts:
            if part.payload_type != "InlineBase64":
                result.warnings.append(
                    ParsedSemanticModelWarning(
                        code="UNSUPPORTED_PAYLOAD_TYPE",
                        message="Only InlineBase64 payloads are supported.",
                        path=part.path,
                    )
                )
                continue

            try:
                text = base64.b64decode(part.payload).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                result.warnings.append(
                    ParsedSemanticModelWarning(
                        code="INVALID_BASE64_PAYLOAD",
                        message="Definition part payload could not be decoded.",
                        path=part.path,
                    )
                )
                continue

            self._parse_tmdl_part(
                text=text,
                result=result,
            )

        return result

    def _parse_tmdl_part(
        self,
        *,
        text: str,
        result: ParsedSemanticModelResponse,
    ) -> None:
        current_table = None
        current_column = None
        current_measure = None
        current_hierarchy = None
        current_relationship = None

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line or line.startswith("//"):
                continue

            if line.startswith("table "):
                current_table = ParsedSemanticModelTable(
                    name=line.removeprefix("table ").strip("' ")
                )
                result.tables.append(current_table)
                current_column = None
                current_measure = None
                current_hierarchy = None
                current_relationship = None
                continue

            if line.startswith("relationship"):
                name = line.removeprefix("relationship").strip() or None
                current_relationship = ParsedSemanticModelRelationship(name=name)
                result.relationships.append(current_relationship)
                current_table = None
                current_column = None
                current_measure = None
                current_hierarchy = None
                continue

            if current_table and line.startswith("column "):
                current_column = ParsedSemanticModelColumn(
                    name=line.removeprefix("column ").strip("' ")
                )
                current_table.columns.append(current_column)
                current_measure = None
                current_hierarchy = None
                continue

            if current_table and line.startswith("measure "):
                name, expression = self._split_assignment(
                    line.removeprefix("measure ").strip()
                )
                current_measure = ParsedSemanticModelMeasure(
                    name=name.strip("' "),
                    expression=expression,
                )
                current_table.measures.append(current_measure)
                current_column = None
                current_hierarchy = None
                continue

            if current_table and line.startswith("hierarchy "):
                current_hierarchy = ParsedSemanticModelHierarchy(
                    name=line.removeprefix("hierarchy ").strip("' ")
                )
                current_table.hierarchies.append(current_hierarchy)
                current_column = None
                current_measure = None
                continue

            if current_hierarchy and line.startswith("level "):
                current_hierarchy.levels.append(
                    ParsedSemanticModelHierarchyLevel(
                        name=line.removeprefix("level ").strip("' ")
                    )
                )
                continue

            key, value = self._split_property(line)

            if current_column:
                self._apply_column_property(current_column, key, value)
            elif current_measure:
                self._apply_measure_property(current_measure, key, value)
            elif current_hierarchy and current_hierarchy.levels:
                if key == "column":
                    current_hierarchy.levels[-1].column = value.strip("' ")
            elif current_relationship:
                self._apply_relationship_property(current_relationship, key, value)

    @staticmethod
    def _split_assignment(value: str) -> tuple[str, str | None]:
        if "=" not in value:
            return value, None

        name, expression = value.split("=", 1)
        return name.strip(), expression.strip()

    @staticmethod
    def _split_property(line: str) -> tuple[str, str]:
        if ":" not in line:
            return "", ""

        key, value = line.split(":", 1)
        return key.strip(), value.strip()

    @staticmethod
    def _to_bool(value: str) -> bool | None:
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        return None

    @staticmethod
    def _parse_field_reference(value: str) -> tuple[str | None, str | None]:
        match = re.match(r"'?([^'\[]+)'?\[([^\]]+)\]", value.strip())
        if not match:
            return None, None

        return match.group(1), match.group(2)

    def _apply_column_property(
        self,
        column: ParsedSemanticModelColumn,
        key: str,
        value: str,
    ) -> None:
        if key == "dataType":
            column.data_type = value
        elif key == "sourceColumn":
            column.source_column = value.strip("' ")
        elif key == "expression":
            column.expression = value
        elif key == "isHidden":
            column.is_hidden = self._to_bool(value)

    def _apply_measure_property(
        self,
        measure: ParsedSemanticModelMeasure,
        key: str,
        value: str,
    ) -> None:
        if key == "expression":
            measure.expression = value
        elif key == "formatString":
            measure.format_string = value.strip("' ")
        elif key == "isHidden":
            measure.is_hidden = self._to_bool(value)

    def _apply_relationship_property(
        self,
        relationship: ParsedSemanticModelRelationship,
        key: str,
        value: str,
    ) -> None:
        if key == "fromColumn":
            relationship.from_table, relationship.from_column = (
                self._parse_field_reference(value)
            )
        elif key == "toColumn":
            relationship.to_table, relationship.to_column = (
                self._parse_field_reference(value)
            )
        elif key == "isActive":
            relationship.is_active = self._to_bool(value)
        elif key == "cardinality":
            relationship.cardinality = value
        elif key in {"crossFilteringBehavior", "crossFilterDirection"}:
            relationship.cross_filter_direction = value