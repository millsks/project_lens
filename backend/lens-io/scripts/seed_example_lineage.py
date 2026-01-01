"""Example seed data for lineage graph.

Creates sample nodes and edges to demonstrate the lineage system.
Run with: pixi run python packages/lens-core/scripts/seed_example_lineage.py
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from lens.db.session import async_session_maker, create_async_engine
from lens.lineage.models import (
    Base,
    DataClassification,
    EdgeType,
    LineageEdge,
    LineageNode,
    LineageRun,
    NodeType,
)


async def create_tables():
    """Create all tables in the database."""
    engine = create_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def seed_data(session: AsyncSession):
    """Seed example lineage data.

    Creates a simple pipeline:
    orders_raw (source) → transform_pipeline → orders_clean (stage)
                                            → daily_sales_dashboard
    """
    print("Seeding example lineage data...")

    # 1. Create source datasets
    orders_raw = LineageNode(
        id=uuid4(),
        type=NodeType.SOURCE_TABLE,
        name="orders_raw",
        qualified_name="postgres://prod.raw.orders_raw",
        description="Raw orders data from transactional system",
        system="postgres",
        platform="aws",
        location="postgres://prod-db.company.com:5432/raw",
        classification=DataClassification.CONFIDENTIAL,
        tags={"domain": "sales", "tier": "bronze"},
        attributes={
            "schema": {
                "columns": [
                    {"name": "order_id", "type": "uuid", "nullable": False, "primary_key": True},
                    {"name": "customer_id", "type": "uuid", "nullable": False},
                    {"name": "customer_email", "type": "varchar", "nullable": True, "pii": True},
                    {"name": "order_date", "type": "timestamp", "nullable": False},
                    {"name": "total_amount", "type": "decimal", "nullable": False},
                    {"name": "status", "type": "varchar", "nullable": False},
                ],
            },
            "row_count": 1_500_000,
            "size_bytes": 450_000_000,
            "refresh_schedule": "realtime",
        },
    )

    customers_raw = LineageNode(
        id=uuid4(),
        type=NodeType.SOURCE_TABLE,
        name="customers_raw",
        qualified_name="postgres://prod.raw.customers_raw",
        description="Raw customer master data",
        system="postgres",
        platform="aws",
        classification=DataClassification.PII,
        tags={"domain": "customer", "tier": "bronze"},
        attributes={
            "schema": {
                "columns": [
                    {"name": "customer_id", "type": "uuid", "nullable": False, "primary_key": True},
                    {"name": "customer_email", "type": "varchar", "nullable": False, "pii": True},
                    {"name": "customer_name", "type": "varchar", "nullable": False, "pii": True},
                    {"name": "customer_phone", "type": "varchar", "nullable": True, "pii": True},
                    {"name": "created_at", "type": "timestamp", "nullable": False},
                ],
            },
            "row_count": 250_000,
        },
    )

    # 2. Create transformation pipeline
    transform_pipeline = LineageNode(
        id=uuid4(),
        type=NodeType.PIPELINE,
        name="daily_orders_transform",
        qualified_name="kedro://daily_orders_transform",
        description="Daily pipeline to clean and enrich orders data",
        system="kedro",
        platform="aws",
        tags={"schedule": "daily", "criticality": "high"},
        attributes={
            "language": "python",
            "framework": "kedro",
            "schedule": "0 2 * * *",
            "dependencies": ["pandas", "sqlalchemy"],
        },
    )

    # 3. Create transformed dataset
    orders_clean = LineageNode(
        id=uuid4(),
        type=NodeType.STAGE_TABLE,
        name="orders_clean",
        qualified_name="postgres://prod.stage.orders_clean",
        description="Cleaned and enriched orders with customer info",
        system="postgres",
        platform="aws",
        classification=DataClassification.CONFIDENTIAL,
        tags={"domain": "sales", "tier": "silver"},
        attributes={
            "schema": {
                "columns": [
                    {"name": "order_id", "type": "uuid", "nullable": False, "primary_key": True},
                    {"name": "customer_id", "type": "uuid", "nullable": False},
                    {"name": "customer_name", "type": "varchar", "nullable": False},
                    {"name": "order_date", "type": "date", "nullable": False},
                    {"name": "total_amount", "type": "decimal", "nullable": False},
                    {"name": "status", "type": "varchar", "nullable": False},
                    {"name": "processed_at", "type": "timestamp", "nullable": False},
                ],
            },
            "row_count": 1_480_000,
            "retention_days": 365,
        },
    )

    # 4. Create dashboard consuming the data
    sales_dashboard = LineageNode(
        id=uuid4(),
        type=NodeType.DASHBOARD,
        name="Daily Sales Overview",
        qualified_name="looker://sales/daily_sales_overview",
        description="Executive dashboard showing daily sales metrics",
        system="looker",
        tags={"audience": "executive", "update_frequency": "hourly"},
        attributes={
            "tool": "looker",
            "url": "https://looker.company.com/dashboards/123",
            "owner": "sales-analytics@company.com",
            "viewers": ["CEO", "CFO", "Sales VP"],
            "refresh_frequency": "1 hour",
        },
    )

    # 5. Create team nodes
    data_team = LineageNode(
        id=uuid4(),
        type=NodeType.TEAM,
        name="Data Platform Team",
        description="Data engineering and platform team",
        attributes={
            "email": "data-platform@company.com",
            "slack": "#data-platform",
        },
    )

    sales_team = LineageNode(
        id=uuid4(),
        type=NodeType.TEAM,
        name="Sales Analytics Team",
        description="Sales and revenue analytics",
        attributes={
            "email": "sales-analytics@company.com",
            "slack": "#sales-analytics",
        },
    )

    # Add all nodes
    session.add_all([orders_raw, customers_raw, transform_pipeline, orders_clean, sales_dashboard, data_team, sales_team])
    await session.flush()  # Ensure nodes have IDs

    print(f"Created {6} nodes")

    # 6. Create edges for data flow
    now = datetime.utcnow()

    # Pipeline reads from raw tables
    edge1 = LineageEdge(
        source_id=orders_raw.id,
        target_id=transform_pipeline.id,
        edge_type=EdgeType.READ,
        metadata={"read_mode": "incremental", "partition_column": "order_date"},
        valid_from=now - timedelta(days=30),
    )

    edge2 = LineageEdge(
        source_id=customers_raw.id,
        target_id=transform_pipeline.id,
        edge_type=EdgeType.READ,
        metadata={"read_mode": "full", "join_key": "customer_id"},
        valid_from=now - timedelta(days=30),
    )

    # Pipeline writes to clean table
    edge3 = LineageEdge(
        source_id=transform_pipeline.id,
        target_id=orders_clean.id,
        edge_type=EdgeType.WRITE,
        metadata={
            "write_mode": "overwrite",
            "transformation": "Clean nulls, join customer data, derive metrics",
        },
        valid_from=now - timedelta(days=30),
    )

    # Dashboard consumes clean data
    edge4 = LineageEdge(
        source_id=orders_clean.id,
        target_id=sales_dashboard.id,
        edge_type=EdgeType.CONSUMES,
        metadata={"query_frequency": "hourly", "avg_latency_ms": 250},
        valid_from=now - timedelta(days=30),
    )

    # Ownership edges
    edge5 = LineageEdge(
        source_id=data_team.id,
        target_id=orders_clean.id,
        edge_type=EdgeType.OWNS,
        metadata={"role": "owner", "responsibility": "data quality, schema evolution"},
        valid_from=now - timedelta(days=90),
    )

    edge6 = LineageEdge(
        source_id=sales_team.id,
        target_id=sales_dashboard.id,
        edge_type=EdgeType.OWNS,
        metadata={"role": "owner", "responsibility": "dashboard content, metrics definitions"},
        valid_from=now - timedelta(days=90),
    )

    # Consumption dependency
    edge7 = LineageEdge(
        source_id=sales_team.id,
        target_id=orders_clean.id,
        edge_type=EdgeType.CONSUMES,
        metadata={"sla": "data available by 3am daily"},
        valid_from=now - timedelta(days=60),
    )

    session.add_all([edge1, edge2, edge3, edge4, edge5, edge6, edge7])
    await session.flush()

    print(f"Created {7} edges")

    # 7. Create a pipeline run
    run = LineageRun(
        node_id=transform_pipeline.id,
        run_id="daily_orders_transform_20241231_020000",
        pipeline_name="daily_orders_transform",
        status="success",
        started_at=now - timedelta(hours=2),
        completed_at=now - timedelta(hours=1, minutes=45),
        git_sha="a888fd6c1234567890abcdef",
        git_branch="main",
        environment="prod",
        parameters={"date": "2024-12-31", "mode": "incremental"},
        triggered_by="airflow-scheduler",
        executor="kedro",
        metrics={
            "rows_read_orders": 15_000,
            "rows_read_customers": 250_000,
            "rows_written": 14_800,
            "duration_seconds": 900,
        },
    )

    session.add(run)

    print("Created 1 pipeline run")

    await session.commit()
    print("✅ Seed data committed successfully!")

    # Print summary
    print("\nSummary of created lineage:")
    print(f"  - Source tables: {orders_raw.name}, {customers_raw.name}")
    print(f"  - Pipeline: {transform_pipeline.name}")
    print(f"  - Transformed table: {orders_clean.name}")
    print(f"  - Dashboard: {sales_dashboard.name}")
    print(f"  - Teams: {data_team.name}, {sales_team.name}")
    print("\nYou can now query the lineage API to explore relationships!")


async def main():
    """Main entry point."""
    print("Creating database tables...")
    await create_tables()

    print("\nSeeding example data...")
    session_maker = async_session_maker()
    async with session_maker() as session:
        await seed_data(session)


if __name__ == "__main__":
    asyncio.run(main())
