"""SQLAlchemy models for lineage graph.

Supports the 5 aspects of lineage:
1. Source lineage - where data comes from
2. Transformation lineage - how data is transformed
3. Consumption lineage - where data is used
4. Temporal lineage - how lineage changes over time
5. People & governance - ownership, policies, compliance
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Enums for type safety and clarity


class NodeType(str, Enum):
    """Types of nodes in the lineage graph."""

    # Data assets
    SOURCE_TABLE = "source_table"
    STAGE_TABLE = "stage_table"
    FEATURE_TABLE = "feature_table"
    DIMENSION_TABLE = "dimension_table"
    FACT_TABLE = "fact_table"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"

    # File-based
    FILE = "file"
    DATASET_FILE = "dataset_file"

    # Streaming
    TOPIC = "topic"
    STREAM = "stream"

    # Analytics
    DASHBOARD = "dashboard"
    REPORT = "report"
    CHART = "chart"
    METRIC = "metric"

    # ML
    MODEL = "model"
    FEATURE_SET = "feature_set"
    EXPERIMENT = "experiment"

    # Execution
    PIPELINE = "pipeline"
    PIPELINE_RUN = "pipeline_run"
    JOB = "job"
    NOTEBOOK = "notebook"
    QUERY = "query"

    # API
    API_ENDPOINT = "api_endpoint"
    SERVICE = "service"

    # People & Governance
    PERSON = "person"
    TEAM = "team"
    POLICY = "policy"
    SCHEMA = "schema"


class EdgeType(str, Enum):
    """Types of edges in the lineage graph."""

    # Data flow (core lineage)
    READ = "read"
    WRITE = "write"
    TRANSFORM = "transform"
    DERIVE = "derive"
    COPY = "copy"

    # Column-level
    COLUMN_DERIVES_FROM = "column_derives_from"
    COLUMN_PASSES_THROUGH = "column_passes_through"

    # Consumption
    CONSUMES = "consumes"
    FEEDS = "feeds"
    DEPENDS_ON = "depends_on"

    # Execution
    EXECUTES = "executes"
    PRODUCES = "produces"

    # Governance
    OWNS = "owns"
    STEWARDS = "stewards"
    HAS_POLICY = "has_policy"
    GOVERNED_BY = "governed_by"

    # Organizational
    MEMBER_OF = "member_of"
    REPORTS_TO = "reports_to"


class DataClassification(str, Enum):
    """Data sensitivity classification."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    PHI = "phi"  # Protected Health Information
    PCI = "pci"  # Payment Card Industry


class LineageNode(Base):
    """Node in the lineage graph.

    Represents any entity: dataset, pipeline, dashboard, person, policy, etc.
    Uses JSONB for flexible attributes to accommodate different node types.
    Supports soft deletes and temporal queries via deleted_at.
    """

    __tablename__ = "lineage_nodes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Core identification
    type: Mapped[NodeType] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    qualified_name: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        index=True,
        comment="Fully qualified name, e.g., 'postgres://db.schema.table'",
    )

    # Description and documentation
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # System/location information
    system: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="System identifier, e.g., 'postgres', 's3', 'snowflake'",
    )
    platform: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="Platform, e.g., 'aws', 'gcp', 'azure'",
    )
    location: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Physical location: URI, connection string, etc.",
    )

    # Governance
    classification: Mapped[DataClassification | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    tags: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="User-defined tags for categorization",
    )

    # Flexible attributes for type-specific metadata
    # Examples:
    # - For datasets: {"schema": {...}, "row_count": 1000, "columns": [...]}
    # - For pipelines: {"language": "python", "framework": "kedro"}
    # - For people: {"email": "...", "role": "...", "department": "..."}
    attributes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Type-specific attributes as flexible JSON",
    )

    # Temporal tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp for temporal queries",
    )

    # Relationships
    outgoing_edges: Mapped[list["LineageEdge"]] = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.source_id",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list["LineageEdge"]] = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.target_id",
        back_populates="target",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_node_type_name", "type", "name"),
        Index("idx_node_qualified_name", "qualified_name", postgresql_where="qualified_name IS NOT NULL"),
        Index("idx_node_system_platform", "system", "platform"),
        Index("idx_node_classification", "classification", postgresql_where="classification IS NOT NULL"),
        Index("idx_node_deleted_at", "deleted_at", postgresql_where="deleted_at IS NULL"),
        UniqueConstraint("qualified_name", name="uq_node_qualified_name", postgresql_where="qualified_name IS NOT NULL AND deleted_at IS NULL"),
    )

    def __repr__(self) -> str:
        return f"<LineageNode(id={self.id}, type={self.type}, name={self.name})>"


class LineageEdge(Base):
    """Edge in the lineage graph.

    Represents relationships between nodes with temporal support.
    Stores transformation details, column mappings, and other metadata.
    """

    __tablename__ = "lineage_edges"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Source and target nodes
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Edge type and context
    edge_type: Mapped[EdgeType] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Metadata about the relationship
    # Examples:
    # - For TRANSFORM: {"sql": "...", "code": "...", "parameters": {...}}
    # - For COLUMN_DERIVES_FROM: {"source_column": "...", "target_column": "...", "expression": "..."}
    # - For CONSUMES: {"query_count": 100, "avg_latency_ms": 50}
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Edge-specific metadata and transformation details",
    )

    # Temporal validity (for point-in-time lineage queries)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When this relationship became valid",
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When this relationship became invalid (NULL = still valid)",
    )

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    created_by: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="User or system that created this edge",
    )

    # Relationships
    source: Mapped["LineageNode"] = relationship(
        "LineageNode",
        foreign_keys=[source_id],
        back_populates="outgoing_edges",
    )
    target: Mapped["LineageNode"] = relationship(
        "LineageNode",
        foreign_keys=[target_id],
        back_populates="incoming_edges",
    )

    __table_args__ = (
        Index("idx_edge_source_type", "source_id", "edge_type"),
        Index("idx_edge_target_type", "target_id", "edge_type"),
        Index("idx_edge_temporal", "valid_from", "valid_to"),
        Index("idx_edge_type_temporal", "edge_type", "valid_from", "valid_to"),
        Index("idx_edge_active", "source_id", "target_id", "edge_type", postgresql_where="valid_to IS NULL"),
        # Prevent duplicate active edges
        UniqueConstraint(
            "source_id",
            "target_id",
            "edge_type",
            name="uq_edge_active",
            postgresql_where="valid_to IS NULL",
        ),
    )

    def __repr__(self) -> str:
        return f"<LineageEdge(id={self.id}, type={self.edge_type}, {self.source_id} -> {self.target_id})>"


class ColumnLineage(Base):
    """Column-level lineage tracking.

    Tracks how individual columns flow through transformations.
    Linked to LineageEdges for dataset-level context.
    """

    __tablename__ = "column_lineage"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Link to dataset-level edge
    edge_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lineage_edges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source column
    source_column: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    # Target column
    target_column: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    # Transformation expression (SQL, code, description)
    transformation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="SQL expression, code, or description of transformation",
    )

    # Transformation type
    transformation_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="e.g., 'passthrough', 'cast', 'aggregate', 'join', 'custom'",
    )

    # Confidence score (for ML-derived lineage)
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="Confidence score for automatically inferred lineage (0.0-1.0)",
    )

    # Additional metadata
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Additional column-level metadata",
    )

    # Temporal tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index("idx_column_edge", "edge_id"),
        Index("idx_column_source", "source_column"),
        Index("idx_column_target", "target_column"),
        Index("idx_column_type", "transformation_type", postgresql_where="transformation_type IS NOT NULL"),
        UniqueConstraint("edge_id", "source_column", "target_column", name="uq_column_lineage"),
    )

    def __repr__(self) -> str:
        return f"<ColumnLineage(id={self.id}, {self.source_column} -> {self.target_column})>"


class LineageRun(Base):
    """Execution run metadata.

    Captures details about pipeline/job executions that produced lineage.
    Links to pipeline_run nodes and provides execution context.
    """

    __tablename__ = "lineage_runs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Link to pipeline run node (optional)
    node_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lineage_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Run identification
    run_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="External run ID from orchestrator",
    )
    pipeline_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    # Execution details
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="e.g., 'running', 'success', 'failed'",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Code and environment
    git_sha: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        index=True,
        comment="Git commit SHA for code version",
    )
    git_branch: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    environment: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="e.g., 'dev', 'staging', 'prod'",
    )

    # Parameters and configuration
    parameters: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Pipeline parameters for this run",
    )

    # Execution metadata
    triggered_by: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="User or system that triggered the run",
    )
    executor: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Execution platform, e.g., 'airflow', 'kedro', 'databricks'",
    )

    # Metrics
    metrics: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Run metrics: rows processed, duration, etc.",
    )

    # Error information
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index("idx_run_pipeline_time", "pipeline_name", "started_at"),
        Index("idx_run_status_time", "status", "started_at"),
        Index("idx_run_git_sha", "git_sha", postgresql_where="git_sha IS NOT NULL"),
        Index("idx_run_environment", "environment", postgresql_where="environment IS NOT NULL"),
    )

    def __repr__(self) -> str:
        return f"<LineageRun(id={self.id}, run_id={self.run_id}, status={self.status})>"
