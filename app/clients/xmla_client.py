import asyncio
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Protocol, Self
from urllib.parse import quote

from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    ProviderIntegrationNotConfiguredError,
    UpstreamRequestError,
)

TMSCHEMA_TABLES_QUERY = (
    "SELECT * FROM $SYSTEM.TMSCHEMA_TABLES"
)
TMSCHEMA_COLUMNS_QUERY = (
    "SELECT * FROM $SYSTEM.TMSCHEMA_COLUMNS"
)
TMSCHEMA_MEASURES_QUERY = (
    "SELECT * FROM $SYSTEM.TMSCHEMA_MEASURES"
)
TMSCHEMA_PARTITIONS_QUERY = (
    "SELECT * FROM $SYSTEM.TMSCHEMA_PARTITIONS"
)
TMSCHEMA_HIERARCHIES_QUERY = (
    "SELECT * FROM $SYSTEM.TMSCHEMA_HIERARCHIES"
)
TMSCHEMA_LEVELS_QUERY = (
    "SELECT * FROM $SYSTEM.TMSCHEMA_LEVELS"
)
TMSCHEMA_RELATIONSHIPS_QUERY = (
    "SELECT * FROM $SYSTEM.TMSCHEMA_RELATIONSHIPS"
)


class XmlaMetadataConnection(Protocol):
    def __enter__(self) -> Self:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...

    def execute(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        ...


class XmlaConnectionFactory(Protocol):
    def __call__(
        self,
        *,
        connection_string: str,
        access_token: str,
        adomd_dll_path: str | None,
        token_expires_in_minutes: int,
    ) -> XmlaMetadataConnection:
        ...


class AdomdXmlaConnection:
    def __init__(
        self,
        *,
        connection_string: str,
        access_token: str,
        adomd_dll_path: str | None,
        token_expires_in_minutes: int,
    ) -> None:
        self.connection_string = (
            connection_string
        )
        self.access_token = access_token
        self.adomd_dll_path = (
            adomd_dll_path
        )
        self.token_expires_in_minutes = (
            token_expires_in_minutes
        )
        self._connection: Any = None

    def __enter__(self) -> Self:
        (
            adomd_connection_type,
            access_token_type,
            date_time_offset_type,
        ) = self._load_adomd_types()

        self._connection = adomd_connection_type(
            self.connection_string
        )
        self._connection.AccessToken = (
            access_token_type(
                self.access_token,
                (
                    date_time_offset_type
                    .UtcNow
                    .AddMinutes(
                        self.token_expires_in_minutes
                    )
                ),
                None,
            )
        )
        self._connection.Open()

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._connection is None:
            return

        close = getattr(
            self._connection,
            "Close",
            None,
        )

        if callable(close):
            close()

        dispose = getattr(
            self._connection,
            "Dispose",
            None,
        )

        if callable(dispose):
            dispose()

        self._connection = None

    def execute(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        if self._connection is None:
            raise UpstreamRequestError(
                "xmla",
                detail=(
                    "XMLA connection is not open."
                ),
            )

        command = (
            self._connection
            .CreateCommand()
        )
        command.CommandText = query

        reader = command.ExecuteReader()

        try:
            columns = [
                reader.GetName(index)
                for index in range(
                    reader.FieldCount
                )
            ]
            rows: list[dict[str, Any]] = []

            while reader.Read():
                rows.append(
                    {
                        column: (
                            _normalize_adomd_value(
                                reader.GetValue(
                                    index
                                )
                            )
                        )
                        for index, column
                        in enumerate(columns)
                    }
                )

            return rows

        finally:
            close_reader = getattr(
                reader,
                "Close",
                None,
            )

            if callable(close_reader):
                close_reader()

            dispose_command = getattr(
                command,
                "Dispose",
                None,
            )

            if callable(dispose_command):
                dispose_command()

    def _load_adomd_types(
        self,
    ) -> tuple[Any, Any, Any]:
        try:
            import clr  # type: ignore[import-not-found]

        except ImportError as exc:
            raise ProviderIntegrationNotConfiguredError(
                "xmla",
                detail=(
                    "Install pythonnet and the "
                    "Microsoft Analysis Services "
                    "ADOMD client library, then set "
                    "XMLA_ADOMD_DLL_PATH if the "
                    "assembly is not discoverable."
                ),
            ) from exc

        try:
            if self.adomd_dll_path:
                clr.AddReference(
                    self.adomd_dll_path
                )

            else:
                clr.AddReference(
                    "Microsoft.AnalysisServices."
                    "AdomdClient"
                )

            from Microsoft.AnalysisServices.AdomdClient import (  # type: ignore[import-not-found]
                AccessToken,
                AdomdConnection,
            )
            from System import (  # type: ignore[import-not-found]
                DateTimeOffset,
            )

        except Exception as exc:
            raise ProviderIntegrationNotConfiguredError(
                "xmla",
                detail=(
                    "The Microsoft Analysis Services "
                    "ADOMD client assembly could not "
                    "be loaded. Set XMLA_ADOMD_DLL_PATH "
                    "to the installed "
                    "Microsoft.AnalysisServices."
                    "AdomdClient.dll path."
                ),
            ) from exc

        return (
            AdomdConnection,
            AccessToken,
            DateTimeOffset,
        )


class XmlaClient:
    BASE_ENDPOINT = (
        "powerbi://api.powerbi.com/v1.0"
    )

    def __init__(
        self,
        *,
        connection_factory: (
            XmlaConnectionFactory | None
        ) = None,
        tenant_name: str | None = None,
        adomd_dll_path: str | None = None,
        token_expires_in_minutes: int | None = None,
    ) -> None:
        settings = get_settings()

        self.connection_factory = (
            connection_factory
            or AdomdXmlaConnection
        )
        self.tenant_name = (
            tenant_name
            or settings.xmla_tenant_name
        )
        self.adomd_dll_path = (
            adomd_dll_path
            if adomd_dll_path is not None
            else settings.xmla_adomd_dll_path
        )
        self.token_expires_in_minutes = (
            token_expires_in_minutes
            or settings.xmla_access_token_minutes
        )

    def build_workspace_endpoint(
        self,
        *,
        workspace_id: str,
        workspace_name: str | None = None,
    ) -> str:
        tenant = quote(
            self.tenant_name,
            safe="",
        )
        workspace_target = quote(
            workspace_name or workspace_id,
            safe="",
        )

        return (
            f"{self.BASE_ENDPOINT}/"
            f"{tenant}/"
            f"{workspace_target}"
        )

    def build_connection_string(
        self,
        *,
        workspace_id: str,
        semantic_model_id: str,
        workspace_name: str | None = None,
        database_name: str | None = None,
    ) -> str:
        initial_catalog = (
            database_name or semantic_model_id
        )
        endpoint = self.build_workspace_endpoint(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )
        catalog = _connection_string_value(
            initial_catalog
        )

        return (
            "Data Source="
            f"{endpoint};"
            "Initial Catalog="
            f"{catalog};"
        )

    async def get_semantic_model_metadata(
        self,
        *,
        workspace_id: str,
        semantic_model_id: str,
        access_token: str,
        workspace_name: str | None = None,
        database_name: str | None = None,
    ) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(
                self._get_semantic_model_metadata_sync,
                workspace_id=workspace_id,
                semantic_model_id=semantic_model_id,
                access_token=access_token,
                workspace_name=workspace_name,
                database_name=database_name,
            )

        except AppException:
            raise

        except Exception as exc:
            raise UpstreamRequestError(
                "xmla",
                detail=(
                    _safe_exception_detail(
                        exc,
                        access_token=access_token,
                    )
                ),
            ) from exc

    def _get_semantic_model_metadata_sync(
        self,
        *,
        workspace_id: str,
        semantic_model_id: str,
        access_token: str,
        workspace_name: str | None,
        database_name: str | None,
    ) -> dict[str, Any]:
        connection_string = (
            self.build_connection_string(
                workspace_id=workspace_id,
                semantic_model_id=(
                    semantic_model_id
                ),
                workspace_name=workspace_name,
                database_name=database_name,
            )
        )

        rowsets: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        with self.connection_factory(
            connection_string=connection_string,
            access_token=access_token,
            adomd_dll_path=(
                self.adomd_dll_path
            ),
            token_expires_in_minutes=(
                self.token_expires_in_minutes
            ),
        ) as connection:
            for name, query in _ROWSET_QUERIES.items():
                rowsets[name] = connection.execute(
                    query
                )

        return _metadata_from_rowsets(
            rowsets,
            database_name=database_name,
        )


_ROWSET_QUERIES = {
    "tables": TMSCHEMA_TABLES_QUERY,
    "columns": TMSCHEMA_COLUMNS_QUERY,
    "measures": TMSCHEMA_MEASURES_QUERY,
    "partitions": TMSCHEMA_PARTITIONS_QUERY,
    "hierarchies": TMSCHEMA_HIERARCHIES_QUERY,
    "levels": TMSCHEMA_LEVELS_QUERY,
    "relationships": TMSCHEMA_RELATIONSHIPS_QUERY,
}


def _metadata_from_rowsets(
    rowsets: Mapping[
        str,
        list[dict[str, Any]],
    ],
    *,
    database_name: str | None,
) -> dict[str, Any]:
    warnings: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    tables_by_id: dict[
        str,
        dict[str, Any],
    ] = {}
    columns_by_id: dict[
        str,
        dict[str, Any],
    ] = {}
    hierarchies_by_id: dict[
        str,
        dict[str, Any],
    ] = {}
    pending_sort_columns: list[
        tuple[dict[str, Any], str]
    ] = []

    for table_row in rowsets.get(
        "tables",
        [],
    ):
        table_id = _identifier(
            table_row,
            "ID",
            "TableID",
        )
        table_name = _text(
            table_row,
            "Name",
        )

        if not table_name:
            _add_warning(
                warnings,
                code="XMLA_TABLE_SKIPPED",
                message=(
                    "A table row did not include "
                    "a name."
                ),
                object_name=table_id,
            )
            continue

        table_payload = {
            "name": table_name,
            "description": _text(
                table_row,
                "Description",
            ),
            "is_hidden": _bool(
                table_row,
                "IsHidden",
            ),
            "columns": [],
            "measures": [],
            "partitions": [],
            "hierarchies": [],
        }

        tables.append(table_payload)

        if table_id:
            tables_by_id[table_id] = (
                table_payload
            )

    for column_row in rowsets.get(
        "columns",
        [],
    ):
        table = _table_for_row(
            column_row,
            tables_by_id,
            warnings,
            object_type="column",
        )

        if table is None:
            continue

        column_id = _identifier(
            column_row,
            "ID",
            "ColumnID",
        )
        column_name = (
            _text(
                column_row,
                "ExplicitName",
                "InferredName",
                "Name",
            )
            or _text(
                column_row,
                "SourceColumn",
            )
        )

        if not column_name:
            _add_warning(
                warnings,
                code="XMLA_COLUMN_SKIPPED",
                message=(
                    "A column row did not include "
                    "a name."
                ),
                object_name=column_id,
            )
            continue

        column_payload = {
            "name": column_name,
            "data_type": _text(
                column_row,
                "ExplicitDataType",
                "InferredDataType",
                "DataType",
            ),
            "source_column": _text(
                column_row,
                "SourceColumn",
            ),
            "expression": _text(
                column_row,
                "Expression",
            ),
            "format_string": _text(
                column_row,
                "FormatString",
            ),
            "summarize_by": _text(
                column_row,
                "SummarizeBy",
            ),
            "sort_by_column": _text(
                column_row,
                "SortByColumn",
            ),
            "is_hidden": _bool(
                column_row,
                "IsHidden",
            ),
            "description": _text(
                column_row,
                "Description",
            ),
            "lineage_tag": _text(
                column_row,
                "LineageTag",
            ),
        }

        table["columns"].append(
            column_payload
        )

        if column_id:
            columns_by_id[column_id] = (
                column_payload
            )

        sort_by_column_id = _identifier(
            column_row,
            "SortByColumnID",
            "SortByColumnId",
        )

        if sort_by_column_id:
            pending_sort_columns.append(
                (
                    column_payload,
                    sort_by_column_id,
                )
            )

    for column_payload, sort_by_column_id in (
        pending_sort_columns
    ):
        sort_column = columns_by_id.get(
            sort_by_column_id
        )

        if sort_column:
            column_payload["sort_by_column"] = (
                sort_column["name"]
            )

    for measure_row in rowsets.get(
        "measures",
        [],
    ):
        table = _table_for_row(
            measure_row,
            tables_by_id,
            warnings,
            object_type="measure",
        )

        if table is None:
            continue

        measure_name = _text(
            measure_row,
            "Name",
        )

        if not measure_name:
            _add_warning(
                warnings,
                code="XMLA_MEASURE_SKIPPED",
                message=(
                    "A measure row did not include "
                    "a name."
                ),
            )
            continue

        table["measures"].append(
            {
                "name": measure_name,
                "expression": _text(
                    measure_row,
                    "Expression",
                ),
                "format_string": _text(
                    measure_row,
                    "FormatString",
                ),
                "is_hidden": _bool(
                    measure_row,
                    "IsHidden",
                ),
                "description": _text(
                    measure_row,
                    "Description",
                ),
                "lineage_tag": _text(
                    measure_row,
                    "LineageTag",
                ),
            }
        )

    for partition_row in rowsets.get(
        "partitions",
        [],
    ):
        table = _table_for_row(
            partition_row,
            tables_by_id,
            warnings,
            object_type="partition",
        )

        if table is None:
            continue

        partition_name = _text(
            partition_row,
            "Name",
        )

        if not partition_name:
            _add_warning(
                warnings,
                code="XMLA_PARTITION_SKIPPED",
                message=(
                    "A partition row did not include "
                    "a name."
                ),
            )
            continue

        table["partitions"].append(
            {
                "name": partition_name,
                "mode": _text(
                    partition_row,
                    "Mode",
                ),
                "source_type": _text(
                    partition_row,
                    "SourceType",
                ),
                "expression": _text(
                    partition_row,
                    "Expression",
                ),
                "is_refreshable": _bool(
                    partition_row,
                    "IsRefreshable",
                ),
            }
        )

    for hierarchy_row in rowsets.get(
        "hierarchies",
        [],
    ):
        table = _table_for_row(
            hierarchy_row,
            tables_by_id,
            warnings,
            object_type="hierarchy",
        )

        if table is None:
            continue

        hierarchy_id = _identifier(
            hierarchy_row,
            "ID",
            "HierarchyID",
        )
        hierarchy_name = _text(
            hierarchy_row,
            "Name",
        )

        if not hierarchy_name:
            _add_warning(
                warnings,
                code="XMLA_HIERARCHY_SKIPPED",
                message=(
                    "A hierarchy row did not include "
                    "a name."
                ),
                object_name=hierarchy_id,
            )
            continue

        hierarchy_payload = {
            "name": hierarchy_name,
            "is_hidden": _bool(
                hierarchy_row,
                "IsHidden",
            ),
            "levels": [],
        }
        table["hierarchies"].append(
            hierarchy_payload
        )

        if hierarchy_id:
            hierarchies_by_id[
                hierarchy_id
            ] = hierarchy_payload

    for level_row in rowsets.get(
        "levels",
        [],
    ):
        hierarchy_id = _identifier(
            level_row,
            "HierarchyID",
            "HierarchyId",
        )
        hierarchy = (
            hierarchies_by_id.get(
                hierarchy_id
            )
            if hierarchy_id
            else None
        )

        if hierarchy is None:
            _add_warning(
                warnings,
                code="XMLA_LEVEL_SKIPPED",
                message=(
                    "A hierarchy level row did not "
                    "reference a known hierarchy."
                ),
                object_name=hierarchy_id,
            )
            continue

        column_id = _identifier(
            level_row,
            "ColumnID",
            "ColumnId",
        )
        column = (
            columns_by_id.get(column_id)
            if column_id
            else None
        )
        level_name = _text(
            level_row,
            "Name",
        )

        if not level_name:
            _add_warning(
                warnings,
                code="XMLA_LEVEL_SKIPPED",
                message=(
                    "A hierarchy level row did not "
                    "include a name."
                ),
                object_name=hierarchy_id,
            )
            continue

        hierarchy["levels"].append(
            {
                "name": level_name,
                "column": (
                    column["name"]
                    if column
                    else _text(
                        level_row,
                        "Column",
                    )
                ),
                "ordinal": _int(
                    level_row,
                    "Ordinal",
                ),
            }
        )

    relationships = [
        _map_relationship(
            relationship_row,
            tables_by_id=tables_by_id,
            columns_by_id=columns_by_id,
        )
        for relationship_row in rowsets.get(
            "relationships",
            [],
        )
    ]

    return {
        "database_name": database_name,
        "tables": tables,
        "relationships": relationships,
        "warnings": warnings,
    }


def _map_relationship(
    relationship_row: dict[str, Any],
    *,
    tables_by_id: Mapping[
        str,
        dict[str, Any],
    ],
    columns_by_id: Mapping[
        str,
        dict[str, Any],
    ],
) -> dict[str, Any]:
    from_table_id = _identifier(
        relationship_row,
        "FromTableID",
        "FromTableId",
    )
    from_column_id = _identifier(
        relationship_row,
        "FromColumnID",
        "FromColumnId",
    )
    to_table_id = _identifier(
        relationship_row,
        "ToTableID",
        "ToTableId",
    )
    to_column_id = _identifier(
        relationship_row,
        "ToColumnID",
        "ToColumnId",
    )

    return {
        "name": _text(
            relationship_row,
            "Name",
        ),
        "from_table": _table_name(
            tables_by_id,
            from_table_id,
        ),
        "from_column": _column_name(
            columns_by_id,
            from_column_id,
        ),
        "to_table": _table_name(
            tables_by_id,
            to_table_id,
        ),
        "to_column": _column_name(
            columns_by_id,
            to_column_id,
        ),
        "is_active": _bool(
            relationship_row,
            "IsActive",
        ),
        "cardinality": _text(
            relationship_row,
            "Cardinality",
        ),
        "cross_filter_direction": _text(
            relationship_row,
            "CrossFilteringBehavior",
            "CrossFilterDirection",
        ),
        "security_filtering_behavior": _text(
            relationship_row,
            "SecurityFilteringBehavior",
        ),
    }


def _table_for_row(
    row: dict[str, Any],
    tables_by_id: Mapping[
        str,
        dict[str, Any],
    ],
    warnings: list[dict[str, Any]],
    *,
    object_type: str,
) -> dict[str, Any] | None:
    table_id = _identifier(
        row,
        "TableID",
        "TableId",
    )

    if not table_id:
        _add_warning(
            warnings,
            code=(
                f"XMLA_{object_type.upper()}"
                "_SKIPPED"
            ),
            message=(
                f"A {object_type} row did not "
                "include a table reference."
            ),
        )
        return None

    table = tables_by_id.get(
        table_id
    )

    if table is None:
        _add_warning(
            warnings,
            code=(
                f"XMLA_{object_type.upper()}"
                "_SKIPPED"
            ),
            message=(
                f"A {object_type} row referenced "
                "an unknown table."
            ),
            object_name=table_id,
        )
        return None

    return table


def _row_value(
    row: Mapping[str, Any],
    *keys: str,
) -> Any:
    normalized_keys = {
        _normalize_key(key)
        for key in keys
    }

    for key, value in row.items():
        if (
            _normalize_key(key)
            in normalized_keys
        ):
            return value

    return None


def _normalize_key(
    key: str,
) -> str:
    return (
        key.replace(
            "_",
            "",
        )
        .replace(
            " ",
            "",
        )
        .lower()
    )


def _identifier(
    row: Mapping[str, Any],
    *keys: str,
) -> str | None:
    value = _row_value(
        row,
        *keys,
    )

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def _text(
    row: Mapping[str, Any],
    *keys: str,
) -> str | None:
    value = _row_value(
        row,
        *keys,
    )

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def _bool(
    row: Mapping[str, Any],
    *keys: str,
) -> bool | None:
    value = _row_value(
        row,
        *keys,
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        if value in (0, 1):
            return bool(value)

        return None

    if isinstance(
        value,
        str,
    ):
        normalized = value.strip().lower()

        if normalized in {
            "true",
            "1",
            "yes",
        }:
            return True

        if normalized in {
            "false",
            "0",
            "no",
        }:
            return False

    return None


def _int(
    row: Mapping[str, Any],
    *keys: str,
) -> int | None:
    value = _row_value(
        row,
        *keys,
    )

    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        int,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        try:
            return int(
                value.strip()
            )

        except ValueError:
            return None

    return None


def _table_name(
    tables_by_id: Mapping[
        str,
        dict[str, Any],
    ],
    table_id: str | None,
) -> str | None:
    table = (
        tables_by_id.get(table_id)
        if table_id
        else None
    )

    if table is None:
        return None

    name = table.get("name")

    if isinstance(name, str):
        return name

    return None


def _column_name(
    columns_by_id: Mapping[
        str,
        dict[str, Any],
    ],
    column_id: str | None,
) -> str | None:
    column = (
        columns_by_id.get(column_id)
        if column_id
        else None
    )

    if column is None:
        return None

    name = column.get("name")

    if isinstance(name, str):
        return name

    return None


def _add_warning(
    warnings: list[dict[str, Any]],
    *,
    code: str,
    message: str,
    object_name: str | None = None,
) -> None:
    warnings.append(
        {
            "code": code,
            "message": message,
            "object_name": object_name,
        }
    )


def _connection_string_value(
    value: str,
) -> str:
    if any(
        character in value
        for character in (";", "'")
    ):
        return (
            "'"
            + value.replace(
                "'",
                "''",
            )
            + "'"
        )

    return value


def _normalize_adomd_value(
    value: Any,
) -> Any:
    if value is None:
        return None

    if type(value).__name__ == "DBNull":
        return None

    return value


def _safe_exception_detail(
    exc: Exception,
    *,
    access_token: str,
) -> str | None:
    message = str(exc).strip()

    if not message:
        return None

    if access_token:
        message = message.replace(
            access_token,
            "[redacted]",
        )

    if len(message) > 300:
        return (
            f"{message[:300].rstrip()}..."
        )

    return message
