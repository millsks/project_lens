"""Repository for lineage graph queries.

Provides methods for querying and traversing the lineage graph,
including temporal queries and impact analysis.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, and_, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lens.lineage.models import (
    ColumnLineage,
    EdgeType,
    LineageEdge,
    LineageNode,
    LineageRun,
    NodeType,
)
from lens.lineage.schemas import (
    ColumnLineageCreate,
    LineageEdgeCreate,
    LineageGraphEdge,
    LineageGraphNode,
    LineageGraphResponse,
    LineageNodeCreate,
    LineageNodeUpdate,
    LineageQueryParams,
    LineageRunCreate,
    LineageRunUpdate,
)


class LineageRepository:
    """Repository for lineage graph operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    # Node CRUD operations

    async def create_node(self, node_data: LineageNodeCreate) -> LineageNode:
        """Create a new lineage node.

        Args:
            node_data: Node creation data

        Returns:
            Created lineage node
        """
        node = LineageNode(**node_data.model_dump())
        self.session.add(node)
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def get_node(
        self,
        node_id: UUID | None = None,
        qualified_name: str | None = None,
        include_deleted: bool = False,
    ) -> LineageNode | None:
        """Get a lineage node by ID or qualified name.

        Args:
            node_id: Node UUID
            qualified_name: Fully qualified name
            include_deleted: Whether to include soft-deleted nodes

        Returns:
            LineageNode if found, None otherwise
        """
        conditions = []

        if node_id:
            conditions.append(LineageNode.id == node_id)
        elif qualified_name:
            conditions.append(LineageNode.qualified_name == qualified_name)
        else:
            return None

        if not include_deleted:
            conditions.append(LineageNode.deleted_at.is_(None))

        stmt = select(LineageNode).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_node(self, node_id: UUID, node_data: LineageNodeUpdate) -> LineageNode | None:
        """Update a lineage node.

        Args:
            node_id: Node UUID
            node_data: Update data

        Returns:
            Updated node if found, None otherwise
        """
        node = await self.get_node(node_id=node_id)
        if not node:
            return None

        update_dict = node_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(node, field, value)

        node.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def soft_delete_node(self, node_id: UUID) -> bool:
        """Soft delete a lineage node.

        Args:
            node_id: Node UUID

        Returns:
            True if deleted, False if not found
        """
        node = await self.get_node(node_id=node_id)
        if not node:
            return False

        node.deleted_at = datetime.utcnow()
        await self.session.commit()
        return True

    # Edge CRUD operations

    async def create_edge(self, edge_data: LineageEdgeCreate) -> LineageEdge:
        """Create a new lineage edge.

        Args:
            edge_data: Edge creation data

        Returns:
            Created lineage edge
        """
        edge = LineageEdge(**edge_data.model_dump())
        self.session.add(edge)
        await self.session.commit()
        await self.session.refresh(edge)
        return edge

    async def get_edge(self, edge_id: UUID) -> LineageEdge | None:
        """Get a lineage edge by ID.

        Args:
            edge_id: Edge UUID

        Returns:
            LineageEdge if found, None otherwise
        """
        stmt = select(LineageEdge).where(LineageEdge.id == edge_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def invalidate_edge(self, edge_id: UUID, valid_to: datetime | None = None) -> bool:
        """Invalidate a lineage edge (set valid_to).

        Args:
            edge_id: Edge UUID
            valid_to: Timestamp when edge became invalid (default: now)

        Returns:
            True if invalidated, False if not found
        """
        edge = await self.get_edge(edge_id)
        if not edge:
            return False

        edge.valid_to = valid_to or datetime.utcnow()
        await self.session.commit()
        return True

    # Column lineage operations

    async def create_column_lineage(self, column_data: ColumnLineageCreate) -> ColumnLineage:
        """Create column-level lineage.

        Args:
            column_data: Column lineage creation data

        Returns:
            Created column lineage
        """
        column_lineage = ColumnLineage(**column_data.model_dump())
        self.session.add(column_lineage)
        await self.session.commit()
        await self.session.refresh(column_lineage)
        return column_lineage

    async def get_column_lineage(self, edge_id: UUID) -> list[ColumnLineage]:
        """Get column lineage for an edge.

        Args:
            edge_id: Edge UUID

        Returns:
            List of column lineage entries
        """
        stmt = select(ColumnLineage).where(ColumnLineage.edge_id == edge_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Run operations

    async def create_run(self, run_data: LineageRunCreate) -> LineageRun:
        """Create a lineage run record.

        Args:
            run_data: Run creation data

        Returns:
            Created lineage run
        """
        run = LineageRun(**run_data.model_dump())
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_run(self, run_id: str) -> LineageRun | None:
        """Get a lineage run by run_id.

        Args:
            run_id: External run ID

        Returns:
            LineageRun if found, None otherwise
        """
        stmt = select(LineageRun).where(LineageRun.run_id == run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_run(self, run_id: str, run_data: LineageRunUpdate) -> LineageRun | None:
        """Update a lineage run.

        Args:
            run_id: External run ID
            run_data: Update data

        Returns:
            Updated run if found, None otherwise
        """
        run = await self.get_run(run_id)
        if not run:
            return None

        update_dict = run_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(run, field, value)

        await self.session.commit()
        await self.session.refresh(run)
        return run

    # Graph traversal operations

    async def get_upstream(
        self,
        node_id: UUID,
        depth: int = 3,
        as_of: datetime | None = None,
        edge_types: list[EdgeType] | None = None,
        include_deleted: bool = False,
    ) -> LineageGraphResponse:
        """Get upstream lineage graph.

        Args:
            node_id: Starting node UUID
            depth: Maximum traversal depth
            as_of: Temporal query timestamp
            edge_types: Filter by edge types
            include_deleted: Include soft-deleted nodes

        Returns:
            Graph response with nodes and edges
        """
        return await self._traverse_graph(
            node_id=node_id,
            direction="upstream",
            depth=depth,
            as_of=as_of,
            edge_types=edge_types,
            include_deleted=include_deleted,
        )

    async def get_downstream(
        self,
        node_id: UUID,
        depth: int = 3,
        as_of: datetime | None = None,
        edge_types: list[EdgeType] | None = None,
        include_deleted: bool = False,
    ) -> LineageGraphResponse:
        """Get downstream lineage graph.

        Args:
            node_id: Starting node UUID
            depth: Maximum traversal depth
            as_of: Temporal query timestamp
            edge_types: Filter by edge types
            include_deleted: Include soft-deleted nodes

        Returns:
            Graph response with nodes and edges
        """
        return await self._traverse_graph(
            node_id=node_id,
            direction="downstream",
            depth=depth,
            as_of=as_of,
            edge_types=edge_types,
            include_deleted=include_deleted,
        )

    async def get_bidirectional(
        self,
        node_id: UUID,
        depth: int = 3,
        as_of: datetime | None = None,
        edge_types: list[EdgeType] | None = None,
        include_deleted: bool = False,
    ) -> LineageGraphResponse:
        """Get both upstream and downstream lineage.

        Args:
            node_id: Starting node UUID
            depth: Maximum traversal depth
            as_of: Temporal query timestamp
            edge_types: Filter by edge types
            include_deleted: Include soft-deleted nodes

        Returns:
            Graph response with nodes and edges
        """
        return await self._traverse_graph(
            node_id=node_id,
            direction="both",
            depth=depth,
            as_of=as_of,
            edge_types=edge_types,
            include_deleted=include_deleted,
        )

    async def _traverse_graph(
        self,
        node_id: UUID,
        direction: str,
        depth: int,
        as_of: datetime | None = None,
        edge_types: list[EdgeType] | None = None,
        include_deleted: bool = False,
    ) -> LineageGraphResponse:
        """Internal method for graph traversal using recursive CTE.

        Args:
            node_id: Starting node UUID
            direction: "upstream", "downstream", or "both"
            depth: Maximum traversal depth
            as_of: Temporal query timestamp
            edge_types: Filter by edge types
            include_deleted: Include soft-deleted nodes

        Returns:
            Graph response with nodes and edges
        """
        # Build temporal filter
        timestamp = as_of or datetime.utcnow()

        # Build edge type filter
        edge_type_filter = []
        if edge_types:
            edge_type_filter = [LineageEdge.edge_type.in_(edge_types)]

        # Build recursive CTE for graph traversal
        if direction == "upstream":
            # Traverse from target to source (upstream)
            cte_base = (
                select(
                    LineageEdge.source_id.label("node_id"),
                    LineageEdge.id.label("edge_id"),
                    LineageEdge.source_id,
                    LineageEdge.target_id,
                    LineageEdge.edge_type,
                    LineageEdge.metadata_,
                    literal(1, Integer).label("depth"),
                )
                .where(
                    and_(
                        LineageEdge.target_id == node_id,
                        LineageEdge.valid_from <= timestamp,
                        or_(LineageEdge.valid_to.is_(None), LineageEdge.valid_to > timestamp),
                        *edge_type_filter,
                    )
                )
                .cte(name="lineage_graph", recursive=True)
            )

            cte_recursive = (
                select(
                    LineageEdge.source_id.label("node_id"),
                    LineageEdge.id.label("edge_id"),
                    LineageEdge.source_id,
                    LineageEdge.target_id,
                    LineageEdge.edge_type,
                    LineageEdge.metadata_,
                    (cte_base.c.depth + 1).label("depth"),
                )
                .select_from(LineageEdge)
                .join(cte_base, LineageEdge.target_id == cte_base.c.node_id)
                .where(
                    and_(
                        cte_base.c.depth < depth,
                        LineageEdge.valid_from <= timestamp,
                        or_(LineageEdge.valid_to.is_(None), LineageEdge.valid_to > timestamp),
                        *edge_type_filter,
                    )
                )
            )

        elif direction == "downstream":
            # Traverse from source to target (downstream)
            cte_base = (
                select(
                    LineageEdge.target_id.label("node_id"),
                    LineageEdge.id.label("edge_id"),
                    LineageEdge.source_id,
                    LineageEdge.target_id,
                    LineageEdge.edge_type,
                    LineageEdge.metadata_,
                    literal(1, Integer).label("depth"),
                )
                .where(
                    and_(
                        LineageEdge.source_id == node_id,
                        LineageEdge.valid_from <= timestamp,
                        or_(LineageEdge.valid_to.is_(None), LineageEdge.valid_to > timestamp),
                        *edge_type_filter,
                    )
                )
                .cte(name="lineage_graph", recursive=True)
            )

            cte_recursive = (
                select(
                    LineageEdge.target_id.label("node_id"),
                    LineageEdge.id.label("edge_id"),
                    LineageEdge.source_id,
                    LineageEdge.target_id,
                    LineageEdge.edge_type,
                    LineageEdge.metadata_,
                    (cte_base.c.depth + 1).label("depth"),
                )
                .select_from(LineageEdge)
                .join(cte_base, LineageEdge.source_id == cte_base.c.node_id)
                .where(
                    and_(
                        cte_base.c.depth < depth,
                        LineageEdge.valid_from <= timestamp,
                        or_(LineageEdge.valid_to.is_(None), LineageEdge.valid_to > timestamp),
                        *edge_type_filter,
                    )
                )
            )

        else:  # both directions
            # Combine upstream and downstream traversal
            # This is more complex - for now, make two separate calls
            upstream = await self.get_upstream(node_id, depth, as_of, edge_types, include_deleted)
            downstream = await self.get_downstream(node_id, depth, as_of, edge_types, include_deleted)

            # Merge results
            all_nodes = {n.id: n for n in upstream.nodes + downstream.nodes}
            all_edges = {e.id: e for e in upstream.edges + downstream.edges}

            return LineageGraphResponse(
                query=LineageQueryParams(
                    dataset_id=node_id,
                    direction="both",
                    depth=depth,
                    as_of=as_of,
                    edge_types=edge_types,
                ),
                nodes=list(all_nodes.values()),
                edges=list(all_edges.values()),
                node_count=len(all_nodes),
                edge_count=len(all_edges),
            )

        # Complete the recursive CTE
        cte = cte_base.union_all(cte_recursive)

        # Query for all edges in the graph
        edges_stmt = select(cte.c.edge_id, cte.c.source_id, cte.c.target_id, cte.c.edge_type, cte.c.metadata).distinct()
        edges_result = await self.session.execute(edges_stmt)
        edges_data = edges_result.all()

        # Get all unique node IDs
        node_ids = {node_id}  # Include the starting node
        for edge in edges_data:
            node_ids.add(edge.source_id)
            node_ids.add(edge.target_id)

        # Query for all nodes
        node_conditions = [LineageNode.id.in_(node_ids)]
        if not include_deleted:
            node_conditions.append(LineageNode.deleted_at.is_(None))

        nodes_stmt = select(LineageNode).where(and_(*node_conditions))
        nodes_result = await self.session.execute(nodes_stmt)
        nodes = nodes_result.scalars().all()

        # Convert to response schemas
        graph_nodes = [
            LineageGraphNode(
                id=node.id,
                type=node.type,
                name=node.name,
                qualified_name=node.qualified_name,
                classification=node.classification,
                attributes=node.attributes or {},
                depth=0,  # TODO: Add depth from CTE
            )
            for node in nodes
        ]

        graph_edges = [
            LineageGraphEdge(
                id=edge.edge_id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                edge_type=edge.edge_type,
                metadata=edge.metadata or {},
            )
            for edge in edges_data
        ]

        return LineageGraphResponse(
            query=LineageQueryParams(
                dataset_id=node_id,
                direction=direction,
                depth=depth,
                as_of=as_of,
                edge_types=edge_types,
            ),
            nodes=graph_nodes,
            edges=graph_edges,
            node_count=len(graph_nodes),
            edge_count=len(graph_edges),
        )

    # Convenience query methods

    async def find_nodes_by_type(
        self,
        node_type: NodeType,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[LineageNode]:
        """Find nodes by type.

        Args:
            node_type: Type of nodes to find
            limit: Maximum results
            offset: Offset for pagination
            include_deleted: Include soft-deleted nodes

        Returns:
            List of lineage nodes
        """
        conditions = [LineageNode.type == node_type]
        if not include_deleted:
            conditions.append(LineageNode.deleted_at.is_(None))

        stmt = select(LineageNode).where(and_(*conditions)).limit(limit).offset(offset).order_by(LineageNode.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_nodes(
        self,
        search_term: str,
        node_types: list[NodeType] | None = None,
        limit: int = 50,
    ) -> list[LineageNode]:
        """Search nodes by name or qualified name.

        Args:
            search_term: Search term
            node_types: Filter by node types
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        conditions = [
            or_(
                LineageNode.name.ilike(f"%{search_term}%"),
                LineageNode.qualified_name.ilike(f"%{search_term}%"),
            ),
            LineageNode.deleted_at.is_(None),
        ]

        if node_types:
            conditions.append(LineageNode.type.in_(node_types))

        stmt = select(LineageNode).where(and_(*conditions)).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
