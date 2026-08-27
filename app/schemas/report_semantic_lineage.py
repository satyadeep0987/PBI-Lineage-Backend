from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.normalized_report_definition import (
    VisualFieldReference,
)


class SemanticLineageObject(BaseModel):
    object_type: Literal[
        "column",
        "measure",
        "hierarchy",
        "hierarchy_level",
    ]
    table_name: str
    object_name: str
    hierarchy_name: str | None = None
    level_name: str | None = None


class SemanticLineageFieldMatch(BaseModel):
    page_name: str
    page_display_name: str
    visual_id: str
    visual_title: str | None = None
    visual_type: str | None = None

    field_reference: VisualFieldReference

    status: Literal[
        "matched",
        "unmatched",
    ]
    semantic_object: SemanticLineageObject | None = None
    reason: str | None = None


class ReportSemanticLineageResponse(BaseModel):
    workspace_id: str
    report_id: str
    semantic_model_workspace_id: str
    semantic_model_id: str

    total_field_reference_count: int
    matched_field_reference_count: int
    unmatched_field_reference_count: int

    field_matches: list[SemanticLineageFieldMatch] = Field(
        default_factory=list
    )
    warnings: list[str] = Field(
        default_factory=list
    )
