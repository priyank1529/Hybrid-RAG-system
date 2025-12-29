"""
Neo4j Graph Database Service

This module provides a true graph database backend using Neo4j.
It stores entities and relationships as native graph nodes and edges,
enabling efficient graph traversal and complex graph queries.
"""

from typing import List, Dict, Optional, Tuple
from neo4j import GraphDatabase, Driver
from sqlalchemy.orm import Session

from src.config import get_settings
from src.schemas import GraphResponse, GraphNode, GraphEdge

settings = get_settings()


class Neo4jService:
    """Service for managing knowledge graph in Neo4j."""

    def __init__(self):
        """Initialize Neo4j connection."""
        self.driver: Optional[Driver] = None
        if settings.use_neo4j:
            try:
                self.driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password)
                )
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                print("✅ Neo4j connected successfully")
            except Exception as e:
                print(f"⚠️  Neo4j connection failed: {e}")
                print("   Falling back to SQL-based graph storage")
                self.driver = None

    def __del__(self):
        """Close Neo4j driver on cleanup."""
        if self.driver:
            self.driver.close()

    def is_available(self) -> bool:
        """Check if Neo4j is available."""
        return self.driver is not None

    def create_entity(
        self,
        entity_id: int,
        name: str,
        entity_type: str,
        description: Optional[str],
        document_id: int,
        user_id: int
    ) -> None:
        """
        Create an entity node in Neo4j.

        Args:
            entity_id: Unique entity identifier
            name: Entity name
            entity_type: Type of entity (PERSON, ORG, etc.)
            description: Entity description
            document_id: Source document ID
            user_id: Owner user ID
        """
        if not self.driver:
            return

        with self.driver.session() as session:
            session.run(
                """
                MERGE (e:Entity {id: $entity_id})
                SET e.name = $name,
                    e.type = $entity_type,
                    e.description = $description,
                    e.document_id = $document_id,
                    e.user_id = $user_id
                """,
                entity_id=entity_id,
                name=name,
                entity_type=entity_type,
                description=description or "",
                document_id=document_id,
                user_id=user_id
            )

    def create_relationship(
        self,
        relationship_id: int,
        source_entity_id: int,
        target_entity_id: int,
        relationship_type: str,
        description: Optional[str]
    ) -> None:
        """
        Create a relationship edge in Neo4j.

        Args:
            relationship_id: Unique relationship identifier
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            relationship_type: Type of relationship
            description: Relationship description
        """
        if not self.driver:
            return

        with self.driver.session() as session:
            # Create relationship with dynamic type
            session.run(
                f"""
                MATCH (source:Entity {{id: $source_id}})
                MATCH (target:Entity {{id: $target_id}})
                MERGE (source)-[r:RELATED {{id: $rel_id}}]->(target)
                SET r.type = $rel_type,
                    r.description = $description
                """,
                source_id=source_entity_id,
                target_id=target_entity_id,
                rel_id=relationship_id,
                rel_type=relationship_type,
                description=description or ""
            )

    def get_document_graph(
        self,
        document_id: int
    ) -> GraphResponse:
        """
        Get graph for a specific document.

        Args:
            document_id: Document ID

        Returns:
            Graph with nodes and edges
        """
        if not self.driver:
            return GraphResponse(nodes=[], edges=[])

        with self.driver.session() as session:
            # Get nodes
            nodes_result = session.run(
                """
                MATCH (e:Entity {document_id: $document_id})
                RETURN e.id as id, e.name as name, e.type as type,
                       e.description as description
                """,
                document_id=document_id
            )

            nodes = [
                GraphNode(
                    id=record["id"],
                    name=record["name"],
                    type=record["type"],
                    description=record["description"]
                )
                for record in nodes_result
            ]

            # Get edges
            edges_result = session.run(
                """
                MATCH (source:Entity {document_id: $document_id})-[r:RELATED]->(target:Entity)
                RETURN r.id as id, source.id as source, target.id as target,
                       r.type as type, r.description as description
                """,
                document_id=document_id
            )

            edges = [
                GraphEdge(
                    source=record["source"],
                    target=record["target"],
                    type=record["type"],
                    description=record["description"]
                )
                for record in edges_result
            ]

        return GraphResponse(nodes=nodes, edges=edges)

    def get_user_graph(
        self,
        user_id: int,
        document_ids: Optional[List[int]] = None
    ) -> GraphResponse:
        """
        Get combined graph for user's documents.

        Args:
            user_id: User ID
            document_ids: Optional list of specific document IDs

        Returns:
            Combined graph
        """
        if not self.driver:
            return GraphResponse(nodes=[], edges=[])

        with self.driver.session() as session:
            # Build query with optional document filter
            if document_ids:
                nodes_query = """
                MATCH (e:Entity {user_id: $user_id})
                WHERE e.document_id IN $document_ids
                RETURN e.id as id, e.name as name, e.type as type,
                       e.description as description
                """
                params = {"user_id": user_id, "document_ids": document_ids}
            else:
                nodes_query = """
                MATCH (e:Entity {user_id: $user_id})
                RETURN e.id as id, e.name as name, e.type as type,
                       e.description as description
                """
                params = {"user_id": user_id}

            nodes_result = session.run(nodes_query, params)

            nodes = [
                GraphNode(
                    id=record["id"],
                    name=record["name"],
                    type=record["type"],
                    description=record["description"]
                )
                for record in nodes_result
            ]

            # Get edges
            entity_ids = [node.id for node in nodes]
            if entity_ids:
                edges_result = session.run(
                    """
                    MATCH (source:Entity)-[r:RELATED]->(target:Entity)
                    WHERE source.id IN $entity_ids
                    RETURN r.id as id, source.id as source, target.id as target,
                           r.type as type, r.description as description
                    """,
                    entity_ids=entity_ids
                )

                edges = [
                    GraphEdge(
                        source=record["source"],
                        target=record["target"],
                        type=record["type"],
                        description=record["description"]
                    )
                    for record in edges_result
                ]
            else:
                edges = []

        return GraphResponse(nodes=nodes, edges=edges)

    def find_related_entities(
        self,
        entity_name: str,
        user_id: int,
        max_depth: int = 2
    ) -> List[Dict]:
        """
        Find entities related to a given entity using graph traversal.

        Args:
            entity_name: Name of the entity to search for
            user_id: User ID
            max_depth: Maximum relationship depth to traverse

        Returns:
            List of related entities with their properties
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (start:Entity {user_id: $user_id})
                WHERE start.name CONTAINS $entity_name
                MATCH path = (start)-[:RELATED*1..$max_depth]-(related:Entity)
                RETURN DISTINCT related.id as id, related.name as name,
                       related.type as type, related.description as description,
                       length(path) as distance
                ORDER BY distance
                """,
                user_id=user_id,
                entity_name=entity_name,
                max_depth=max_depth
            )

            return [
                {
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "description": record["description"],
                    "distance": record["distance"]
                }
                for record in result
            ]

    def find_shortest_path(
        self,
        entity1_name: str,
        entity2_name: str,
        user_id: int
    ) -> Optional[List[Dict]]:
        """
        Find shortest path between two entities.

        Args:
            entity1_name: First entity name
            entity2_name: Second entity name
            user_id: User ID

        Returns:
            List of nodes in the path, or None if no path exists
        """
        if not self.driver:
            return None

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e1:Entity {user_id: $user_id})
                WHERE e1.name CONTAINS $entity1_name
                MATCH (e2:Entity {user_id: $user_id})
                WHERE e2.name CONTAINS $entity2_name
                MATCH path = shortestPath((e1)-[:RELATED*]-(e2))
                RETURN [node in nodes(path) | {
                    id: node.id,
                    name: node.name,
                    type: node.type
                }] as path
                LIMIT 1
                """,
                user_id=user_id,
                entity1_name=entity1_name,
                entity2_name=entity2_name
            )

            record = result.single()
            return record["path"] if record else None

    def delete_document_graph(
        self,
        document_id: int
    ) -> None:
        """
        Delete all entities and relationships for a document.

        Args:
            document_id: Document ID
        """
        if not self.driver:
            return

        with self.driver.session() as session:
            session.run(
                """
                MATCH (e:Entity {document_id: $document_id})
                DETACH DELETE e
                """,
                document_id=document_id
            )

    def get_statistics(
        self,
        user_id: int
    ) -> Dict:
        """
        Get graph statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with graph statistics
        """
        if not self.driver:
            return {"entities": 0, "relationships": 0, "documents": 0}

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity {user_id: $user_id})
                WITH COUNT(DISTINCT e) as entity_count,
                     COUNT(DISTINCT e.document_id) as doc_count
                MATCH (e1:Entity {user_id: $user_id})-[r:RELATED]->()
                RETURN entity_count, COUNT(r) as rel_count, doc_count
                """,
                user_id=user_id
            )

            record = result.single()
            if record:
                return {
                    "entities": record["entity_count"],
                    "relationships": record["rel_count"],
                    "documents": record["doc_count"]
                }
            else:
                return {"entities": 0, "relationships": 0, "documents": 0}


# Global Neo4j service instance
neo4j_service = Neo4jService()
