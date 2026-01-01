"""Initial lineage schema

Revision ID: 001
Revises:
Create Date: 2024-12-31 15:00:00.000000

Creates the initial lineage graph schema with support for:
- Nodes (datasets, pipelines, dashboards, people, policies)
- Edges (relationships with temporal support)
- Column-level lineage
- Run tracking
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create lineage_nodes table
    op.create_table(
        "lineage_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("qualified_name", sa.String(length=1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("documentation_url", sa.String(length=1000), nullable=True),
        sa.Column("system", sa.String(length=200), nullable=True),
        sa.Column("platform", sa.String(length=200), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("classification", sa.String(length=50), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "qualified_name",
            name="uq_node_qualified_name",
            postgresql_where=sa.text("qualified_name IS NOT NULL AND deleted_at IS NULL"),
        ),
    )

    # Create indexes for lineage_nodes
    op.create_index("idx_node_type_name", "lineage_nodes", ["type", "name"])
    op.create_index(
        "idx_node_qualified_name",
        "lineage_nodes",
        ["qualified_name"],
        postgresql_where=sa.text("qualified_name IS NOT NULL"),
    )
    op.create_index("idx_node_system_platform", "lineage_nodes", ["system", "platform"])
    op.create_index(
        "idx_node_classification",
        "lineage_nodes",
        ["classification"],
        postgresql_where=sa.text("classification IS NOT NULL"),
    )
    op.create_index(
        "idx_node_deleted_at",
        "lineage_nodes",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(op.f("ix_lineage_nodes_type"), "lineage_nodes", ["type"])
    op.create_index(op.f("ix_lineage_nodes_name"), "lineage_nodes", ["name"])
    op.create_index(op.f("ix_lineage_nodes_created_at"), "lineage_nodes", ["created_at"])

    # Create lineage_edges table
    op.create_table(
        "lineage_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edge_type", sa.String(length=50), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["lineage_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_id"],
            ["lineage_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "target_id",
            "edge_type",
            name="uq_edge_active",
            postgresql_where=sa.text("valid_to IS NULL"),
        ),
    )

    # Create indexes for lineage_edges
    op.create_index("idx_edge_source_type", "lineage_edges", ["source_id", "edge_type"])
    op.create_index("idx_edge_target_type", "lineage_edges", ["target_id", "edge_type"])
    op.create_index("idx_edge_temporal", "lineage_edges", ["valid_from", "valid_to"])
    op.create_index("idx_edge_type_temporal", "lineage_edges", ["edge_type", "valid_from", "valid_to"])
    op.create_index(
        "idx_edge_active",
        "lineage_edges",
        ["source_id", "target_id", "edge_type"],
        postgresql_where=sa.text("valid_to IS NULL"),
    )
    op.create_index(op.f("ix_lineage_edges_source_id"), "lineage_edges", ["source_id"])
    op.create_index(op.f("ix_lineage_edges_target_id"), "lineage_edges", ["target_id"])
    op.create_index(op.f("ix_lineage_edges_edge_type"), "lineage_edges", ["edge_type"])
    op.create_index(op.f("ix_lineage_edges_valid_from"), "lineage_edges", ["valid_from"])
    op.create_index(op.f("ix_lineage_edges_valid_to"), "lineage_edges", ["valid_to"])

    # Create column_lineage table
    op.create_table(
        "column_lineage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_column", sa.String(length=500), nullable=False),
        sa.Column("target_column", sa.String(length=500), nullable=False),
        sa.Column("transformation", sa.Text(), nullable=True),
        sa.Column("transformation_type", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["edge_id"],
            ["lineage_edges.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("edge_id", "source_column", "target_column", name="uq_column_lineage"),
    )

    # Create indexes for column_lineage
    op.create_index("idx_column_edge", "column_lineage", ["edge_id"])
    op.create_index("idx_column_source", "column_lineage", ["source_column"])
    op.create_index("idx_column_target", "column_lineage", ["target_column"])
    op.create_index(
        "idx_column_type",
        "column_lineage",
        ["transformation_type"],
        postgresql_where=sa.text("transformation_type IS NOT NULL"),
    )

    # Create lineage_runs table
    op.create_table(
        "lineage_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_id", sa.String(length=200), nullable=False),
        sa.Column("pipeline_name", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("git_sha", sa.String(length=40), nullable=True),
        sa.Column("git_branch", sa.String(length=200), nullable=True),
        sa.Column("environment", sa.String(length=50), nullable=True),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("triggered_by", sa.String(length=200), nullable=True),
        sa.Column("executor", sa.String(length=200), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["node_id"],
            ["lineage_nodes.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )

    # Create indexes for lineage_runs
    op.create_index("idx_run_pipeline_time", "lineage_runs", ["pipeline_name", "started_at"])
    op.create_index("idx_run_status_time", "lineage_runs", ["status", "started_at"])
    op.create_index(
        "idx_run_git_sha",
        "lineage_runs",
        ["git_sha"],
        postgresql_where=sa.text("git_sha IS NOT NULL"),
    )
    op.create_index(
        "idx_run_environment",
        "lineage_runs",
        ["environment"],
        postgresql_where=sa.text("environment IS NOT NULL"),
    )
    op.create_index(op.f("ix_lineage_runs_run_id"), "lineage_runs", ["run_id"], unique=True)
    op.create_index(op.f("ix_lineage_runs_pipeline_name"), "lineage_runs", ["pipeline_name"])
    op.create_index(op.f("ix_lineage_runs_status"), "lineage_runs", ["status"])
    op.create_index(op.f("ix_lineage_runs_started_at"), "lineage_runs", ["started_at"])


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("lineage_runs")
    op.drop_table("column_lineage")
    op.drop_table("lineage_edges")
    op.drop_table("lineage_nodes")
