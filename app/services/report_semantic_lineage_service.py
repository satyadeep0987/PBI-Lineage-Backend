from app.schemas.normalized_report_definition import (
    NormalizedReportDefinitionResponse,
    VisualFieldReference,
)
from app.schemas.parsed_semantic_model import (
    ParsedSemanticModelHierarchy,
    ParsedSemanticModelResponse,
    ParsedSemanticModelTable,
)
from app.schemas.report_semantic_lineage import (
    ReportSemanticLineageResponse,
    SemanticLineageFieldMatch,
    SemanticLineageObject,
)
from app.services.report_definition_service import (
    ReportDefinitionService,
)
from app.services.semantic_model_definition_service import (
    SemanticModelDefinitionService,
)


class ReportSemanticLineageService:
    def __init__(self) -> None:
        self.report_definition_service = (
            ReportDefinitionService()
        )
        self.semantic_model_definition_service = (
            SemanticModelDefinitionService()
        )

    async def build_lineage(
        self,
        *,
        workspace_id: str,
        report_id: str,
        semantic_model_workspace_id: str,
        semantic_model_id: str,
        access_token: str,
        report_definition_format: str | None = "TMDL",
        semantic_model_definition_format: str = "TMDL",
    ) -> ReportSemanticLineageResponse:
        report = await (
            self.report_definition_service
            .get_normalized_definition(
                workspace_id=workspace_id,
                report_id=report_id,
                access_token=access_token,
                definition_format=(
                    report_definition_format
                ),
            )
        )

        semantic_model = await (
            self.semantic_model_definition_service
            .get_parsed_definition(
                workspace_id=(
                    semantic_model_workspace_id
                ),
                semantic_model_id=semantic_model_id,
                access_token=access_token,
                definition_format=(
                    semantic_model_definition_format
                ),
            )
        )

        return self.match(
            report=report,
            semantic_model=semantic_model,
            semantic_model_workspace_id=(
                semantic_model_workspace_id
            ),
        )

    def match(
        self,
        *,
        report: NormalizedReportDefinitionResponse,
        semantic_model: ParsedSemanticModelResponse,
        semantic_model_workspace_id: str,
    ) -> ReportSemanticLineageResponse:
        index = _SemanticModelIndex(
            semantic_model
        )

        field_matches: list[
            SemanticLineageFieldMatch
        ] = []

        for page in report.pages:
            for visual in page.visuals:
                for field_reference in (
                    visual.field_references
                ):
                    (
                        semantic_object,
                        reason,
                    ) = index.find(
                        field_reference
                    )

                    status = (
                        "matched"
                        if semantic_object is not None
                        else "unmatched"
                    )

                    field_matches.append(
                        SemanticLineageFieldMatch(
                            page_name=page.name,
                            page_display_name=(
                                page.display_name
                            ),
                            visual_id=visual.id,
                            visual_title=(
                                visual.title
                            ),
                            visual_type=(
                                visual.visual_type
                            ),
                            field_reference=(
                                field_reference
                            ),
                            status=status,
                            semantic_object=(
                                semantic_object
                            ),
                            reason=reason,
                        )
                    )

        matched_count = sum(
            1
            for field_match in field_matches
            if field_match.status == "matched"
        )

        warnings = list(
            report.warnings
        )
        warnings.extend(
            self._semantic_model_warnings(
                semantic_model
            )
        )

        return ReportSemanticLineageResponse(
            workspace_id=report.workspace_id,
            report_id=report.report_id,
            semantic_model_workspace_id=(
                semantic_model_workspace_id
            ),
            semantic_model_id=(
                semantic_model.semantic_model_id
            ),
            total_field_reference_count=len(
                field_matches
            ),
            matched_field_reference_count=(
                matched_count
            ),
            unmatched_field_reference_count=(
                len(field_matches)
                - matched_count
            ),
            field_matches=field_matches,
            warnings=warnings,
        )

    @staticmethod
    def _semantic_model_warnings(
        semantic_model: ParsedSemanticModelResponse,
    ) -> list[str]:
        warnings: list[str] = []

        for warning in semantic_model.warnings:
            message = (
                f"{warning.code}: "
                f"{warning.message}"
            )

            if warning.path:
                message = (
                    f"{message} "
                    f"({warning.path})"
                )

            warnings.append(message)

        return warnings


class _SemanticModelIndex:
    def __init__(
        self,
        semantic_model: ParsedSemanticModelResponse,
    ) -> None:
        self.tables = {
            _key(table.name): table
            for table in semantic_model.tables
        }
        self.columns = (
            self._build_column_index(
                semantic_model
            )
        )
        self.measures = (
            self._build_measure_index(
                semantic_model
            )
        )
        self.hierarchies = (
            self._build_hierarchy_index(
                semantic_model
            )
        )
        self.hierarchy_levels = (
            self._build_hierarchy_level_index(
                semantic_model
            )
        )

    def find(
        self,
        reference: VisualFieldReference,
    ) -> tuple[
        SemanticLineageObject | None,
        str | None,
    ]:
        table_name = reference.table_name
        object_name = reference.object_name

        if not table_name:
            return None, "missing_table_name"

        if _key(table_name) not in self.tables:
            return None, "table_not_found"

        if reference.object_type == "column":
            if not object_name:
                return None, "missing_object_name"

            result = self.columns.get(
                (
                    _key(table_name),
                    _key(object_name),
                )
            )

            return (
                result,
                None
                if result is not None
                else "object_not_found",
            )

        if reference.object_type == "measure":
            if not object_name:
                return None, "missing_object_name"

            result = self.measures.get(
                (
                    _key(table_name),
                    _key(object_name),
                )
            )

            return (
                result,
                None
                if result is not None
                else "object_not_found",
            )

        if reference.object_type == "hierarchy":
            hierarchy_name = (
                reference.hierarchy_name
                or object_name
            )

            if not hierarchy_name:
                return None, "missing_object_name"

            result = self.hierarchies.get(
                (
                    _key(table_name),
                    _key(hierarchy_name),
                )
            )

            return (
                result,
                None
                if result is not None
                else "object_not_found",
            )

        if reference.object_type == "hierarchy_level":
            result = self._find_hierarchy_level(
                reference
            )

            return (
                result,
                None
                if result is not None
                else "object_not_found",
            )

        return None, "unsupported_object_type"

    def _find_hierarchy_level(
        self,
        reference: VisualFieldReference,
    ) -> SemanticLineageObject | None:
        if (
            not reference.table_name
            or not reference.hierarchy_name
            or not reference.level_name
        ):
            return None

        return self.hierarchy_levels.get(
            (
                _key(reference.table_name),
                _key(reference.hierarchy_name),
                _key(reference.level_name),
            )
        )

    @staticmethod
    def _build_column_index(
        semantic_model: ParsedSemanticModelResponse,
    ) -> dict[
        tuple[str, str],
        SemanticLineageObject,
    ]:
        index: dict[
            tuple[str, str],
            SemanticLineageObject,
        ] = {}

        for table in semantic_model.tables:
            for column in table.columns:
                lineage_object = (
                    SemanticLineageObject(
                        object_type="column",
                        table_name=table.name,
                        object_name=column.name,
                    )
                )

                index[
                    (
                        _key(table.name),
                        _key(column.name),
                    )
                ] = lineage_object

                if column.source_column:
                    index.setdefault(
                        (
                            _key(table.name),
                            _key(
                                column.source_column
                            ),
                        ),
                        lineage_object,
                    )

        return index

    @staticmethod
    def _build_measure_index(
        semantic_model: ParsedSemanticModelResponse,
    ) -> dict[
        tuple[str, str],
        SemanticLineageObject,
    ]:
        index: dict[
            tuple[str, str],
            SemanticLineageObject,
        ] = {}

        for table in semantic_model.tables:
            for measure in table.measures:
                index[
                    (
                        _key(table.name),
                        _key(measure.name),
                    )
                ] = SemanticLineageObject(
                    object_type="measure",
                    table_name=table.name,
                    object_name=measure.name,
                )

        return index

    @staticmethod
    def _build_hierarchy_index(
        semantic_model: ParsedSemanticModelResponse,
    ) -> dict[
        tuple[str, str],
        SemanticLineageObject,
    ]:
        index: dict[
            tuple[str, str],
            SemanticLineageObject,
        ] = {}

        for table in semantic_model.tables:
            for hierarchy in table.hierarchies:
                index[
                    (
                        _key(table.name),
                        _key(hierarchy.name),
                    )
                ] = SemanticLineageObject(
                    object_type="hierarchy",
                    table_name=table.name,
                    object_name=hierarchy.name,
                    hierarchy_name=hierarchy.name,
                )

        return index

    @staticmethod
    def _build_hierarchy_level_index(
        semantic_model: ParsedSemanticModelResponse,
    ) -> dict[
        tuple[str, str, str],
        SemanticLineageObject,
    ]:
        index: dict[
            tuple[str, str, str],
            SemanticLineageObject,
        ] = {}

        for table in semantic_model.tables:
            _SemanticModelIndex._index_table_hierarchies(
                index=index,
                table=table,
            )

        return index

    @staticmethod
    def _index_table_hierarchies(
        *,
        index: dict[
            tuple[str, str, str],
            SemanticLineageObject,
        ],
        table: ParsedSemanticModelTable,
    ) -> None:
        for hierarchy in table.hierarchies:
            _SemanticModelIndex._index_hierarchy_levels(
                index=index,
                table=table,
                hierarchy=hierarchy,
            )

    @staticmethod
    def _index_hierarchy_levels(
        *,
        index: dict[
            tuple[str, str, str],
            SemanticLineageObject,
        ],
        table: ParsedSemanticModelTable,
        hierarchy: ParsedSemanticModelHierarchy,
    ) -> None:
        for level in hierarchy.levels:
            lineage_object = SemanticLineageObject(
                object_type="hierarchy_level",
                table_name=table.name,
                object_name=level.name,
                hierarchy_name=hierarchy.name,
                level_name=level.name,
            )

            index[
                (
                    _key(table.name),
                    _key(hierarchy.name),
                    _key(level.name),
                )
            ] = lineage_object


def _key(
    value: str,
) -> str:
    return value.strip().casefold()
