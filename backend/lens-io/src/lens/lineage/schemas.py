"""Pydantic schemas for lineage API contracts.

These schemas define the structure for API requests/responses
and provide validation for lineage data.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from lens.lineage.models import DataClassification, EdgeType, NodeType

# Node Schemas


class LineageNodeBase(BaseModel):
    """Base schema for lineage nodes."""

    type: NodeType
    name: str = Field(..., max_length=500)
    qualified_name: str | None = Field(None, max_length=1000)
    description: str | None = None
    documentation_url: str | None = Field(None, max_length=1000)
    system: str | None = Field(None, max_length=200)
    platform: str | None = Field(None, max_length=200)
    location: str | None = None
    classification: DataClassification | None = None
    tags: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)


class LineageNodeCreate(LineageNodeBase):
    """Schema for creating a lineage node."""

    pass


class LineageNodeUpdate(BaseModel):
    """Schema for updating a lineage node."""

    name: str | None = Field(None, max_length=500)
    description: str | None = None
    documentation_url: str | None = Field(None, max_length=1000)
    classification: DataClassification | None = None
    tags: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None


class LineageNodeResponse(LineageNodeBase):
    """Schema for lineage node responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Edge Schemas


class LineageEdgeBase(BaseModel):
    """Base schema for lineage edges."""

    source_id: UUID
    target_id: UUID
    edge_type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: datetime | None = None


class LineageEdgeCreate(LineageEdgeBase):
    """Schema for creating a lineage edge."""

    created_by: str | None = Field(None, max_length=200)


class LineageEdgeResponse(LineageEdgeBase):
    """Schema for lineage edge responses."""

    id: UUID
    created_at: datetime
    created_by: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Column Lineage Schemas


class ColumnLineageBase(BaseModel):
    """Base schema for column lineage."""

    source_column: str = Field(..., max_length=500)
    target_column: str = Field(..., max_length=500)
    transformation: str | None = None
    transformation_type: str | None = Field(None, max_length=50)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ColumnLineageCreate(ColumnLineageBase):
    """Schema for creating column lineage."""

    edge_id: UUID


class ColumnLineageResponse(ColumnLineageBase):
    """Schema for column lineage responses."""

    id: UUID
    edge_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Run Schemas


class LineageRunBase(BaseModel):
    """Base schema for lineage runs."""

    run_id: str = Field(..., max_length=200)
    pipeline_name: str = Field(..., max_length=500)
    status: str = Field(..., max_length=50)
    started_at: datetime
    completed_at: datetime | None = None
    git_sha: str | None = Field(None, max_length=40)
    git_branch: str | None = Field(None, max_length=200)
    environment: str | None = Field(None, max_length=50)
    parameters: dict[str, Any] = Field(default_factory=dict)
    triggered_by: str | None = Field(None, max_length=200)
    executor: str | None = Field(None, max_length=200)
    metrics: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class LineageRunCreate(LineageRunBase):
    """Schema for creating a lineage run."""

    node_id: UUID | None = None


class LineageRunUpdate(BaseModel):
    """Schema for updating a lineage run."""

    status: str | None = Field(None, max_length=50)
    completed_at: datetime | None = None
    metrics: dict[str, Any] | None = None
    error_message: str | None = None


class LineageRunResponse(LineageRunBase):
    """Schema for lineage run responses."""

    id: UUID
    node_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Graph Query Schemas


class LineageQueryParams(BaseModel):
    """Parameters for lineage graph queries."""

    dataset_id: UUID | None = None
    dataset_name: str | None = None
    direction: str = Field("both", pattern="^(upstream|downstream|both)$")
    depth: int = Field(3, ge=1, le=10)
    as_of: datetime | None = None
    include_deleted: bool = False
    edge_types: list[EdgeType] | None = None


class LineageGraphNode(BaseModel):
    """Node in a lineage graph response."""

    id: UUID
    type: NodeType
    name: str
    qualified_name: str | None = None
    classification: DataClassification | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    depth: int = Field(0, description="Distance from query root")


class LineageGraphEdge(BaseModel):
    """Edge in a lineage graph response."""

    id: UUID
    source_id: UUID
    target_id: UUID
    edge_type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineageGraphResponse(BaseModel):
    """Response for lineage graph queries."""

    query: LineageQueryParams
    nodes: list[LineageGraphNode]
    edges: list[LineageGraphEdge]
    node_count: int
    edge_count: int


# Impact Analysis Schemas


class ImpactAnalysisRequest(BaseModel):
    """Request for impact analysis."""

    action: str = Field(..., description="Action type: DELETE_DATASET, DROP_COLUMN, CHANGE_SCHEMA, etc.")
    target_id: UUID | None = None
    target_name: str | None = None
    target_column: str | None = None
    as_of: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict, description="Additional context for the change")


class ImpactSummary(BaseModel):
    """Summary of impact for a specific aspect."""

    aspect: str = Field(..., description="One of: source, transformation, consumption, temporal, governance")
    severity: str = Field(..., pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$")
    affected_count: int
    description: str


class ImpactAnalysisResponse(BaseModel):
    """Response for impact analysis."""

    request: ImpactAnalysisRequest
    summary: str
    impacts_by_aspect: dict[str, list[ImpactSummary]]
    affected_nodes: list[LineageGraphNode]
    affected_edges: list[LineageGraphEdge]
    recommended_actions: list[str]
    affected_people: list[str] = Field(default_factory=list)


# Dataset Schema (convenience schemas for common use cases)


class DatasetSchema(BaseModel):
    """Schema information for a dataset."""

    columns: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of column definitions with name, type, nullable, etc.",
    )
    primary_keys: list[str] = Field(default_factory=list)
    foreign_keys: list[dict[str, Any]] = Field(default_factory=list)
    indexes: list[dict[str, Any]] = Field(default_factory=list)
    partitions: list[str] | None = None


class DatasetAttributes(BaseModel):
    """Common attributes for dataset nodes."""

    dataset_schema: DatasetSchema | None = None
    row_count: int | None = None
    size_bytes: int | None = None
    last_modified: datetime | None = None
    refresh_schedule: str | None = None
    retention_days: int | None = None


class PipelineAttributes(BaseModel):
    """Common attributes for pipeline nodes."""

    language: str | None = None
    framework: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    schedule: str | None = None
    timeout_seconds: int | None = None
    retry_count: int | None = None


class DashboardAttributes(BaseModel):
    """Common attributes for dashboard nodes."""

    tool: str | None = None  # e.g., "looker", "tableau", "powerbi"
    url: str | None = None
    owner: str | None = None
    viewers: list[str] = Field(default_factory=list)
    refresh_frequency: str | None = None
