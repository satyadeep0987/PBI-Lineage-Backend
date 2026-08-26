from typing import Literal

from pydantic import BaseModel


class SemanticModelReference(BaseModel):
    mode: Literal[
        "by_connection",
        "by_path",
        "unknown",
    ]

    semantic_model_id: str | None = None
    path: str | None = None


class NormalizedVisualPosition(BaseModel):
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    z: float | None = None
    tab_order: float | None = None


class NormalizedReportVisual(BaseModel):
    id: str

    internal_name: str

    title: str | None = None
    title_visible: bool | None = None
    title_is_dynamic: bool = False

    visual_type: str | None = None

    parent_group_name: str | None = None
    is_hidden: bool = False

    has_query: bool = False

    position: (
        NormalizedVisualPosition | None
    ) = None

class NormalizedReportPage(BaseModel):
    name: str
    display_name: str

    order: int | None = None
    is_active: bool = False

    display_option: str | None = None

    width: float | None = None
    height: float | None = None

    visuals: list[
        NormalizedReportVisual
    ]

    visual_count: int


class NormalizedReportDefinitionResponse(
    BaseModel
):
    workspace_id: str
    report_id: str

    format: Literal[
        "PBIR",
        "PBIR-Legacy",
        "Unknown",
    ]

    definition_version: str | None = None

    semantic_model: (
        SemanticModelReference | None
    ) = None

    pages: list[
        NormalizedReportPage
    ]

    page_count: int
    visual_count: int

    source_part_count: int
    decoded_json_part_count: int

    warnings: list[str]