from typing import Literal

from pydantic import BaseModel, Field


class SnowflakeObjectReference(BaseModel):
    object_id: str
    database: str
    schema_name: str
    object_name: str
    object_domain: str
    qualified_name: str


class SnowflakeDependency(BaseModel):
    source: SnowflakeObjectReference
    target: SnowflakeObjectReference
    dependency_type: str


class SnowflakeLineageWarning(BaseModel):
    code: str
    message: str
    row_index: int | None = None


class SnowflakeLineageSnapshot(BaseModel):
    account_identifier: str
    objects: list[SnowflakeObjectReference] = Field(default_factory=list)
    dependencies: list[SnowflakeDependency] = Field(default_factory=list)
    warnings: list[SnowflakeLineageWarning] = Field(default_factory=list)
    object_count: int = 0
    dependency_count: int = 0


class SnowflakeLineageRowsRequest(BaseModel):
    account_identifier: str
    rows: list[dict[str, object]] = Field(default_factory=list)


class SnowflakeLineageDiscoveryRequest(BaseModel):
    account_identifier: str
    warehouse: str | None = None
    role: str | None = None
    token_type: Literal[
        "OAUTH",
        "KEYPAIR_JWT",
        "PROGRAMMATIC_ACCESS_TOKEN",
    ] = "OAUTH"
