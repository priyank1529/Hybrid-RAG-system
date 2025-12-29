import re
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document

from src.config import get_settings
from src.models import Entity, Relationship, Document as DBDocument
from src.schemas import GraphResponse, GraphNode, GraphEdge
from src.graphdb.neo4j_service import neo4j_service

settings = get_settings()


class GraphRAGService:
    """Service for Graph-based RAG with entity extraction."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.google_api_key,
            temperature=0
        )

    def extract_entities_and_relationships(
        self,
        text: str,
        document_id: int,
        db: Session
    ) -> Tuple[List[Entity], List[Relationship]]:
        """
        Extract entities and relationships from text using LLM.

        Args:
            text: Text to extract from
            document_id: Document ID
            db: Database session

        Returns:
            Tuple of (entities, relationships)
        """
        prompt = f"""Extract entities and relationships from the following text.

Text: {text}

Please identify:
1. Entities: People, Organizations, Locations, Technologies, Concepts
2. Relationships: How entities relate to each other

Format your response as:
ENTITIES:
- [TYPE] Name: Description

RELATIONSHIPS:
- Source Entity -> Relationship Type -> Target Entity: Description

Be specific and extract all meaningful entities and relationships."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            entities = self._parse_entities(content, document_id, db)
            relationships = self._parse_relationships(content, entities, db)

            return entities, relationships

        except Exception as e:
            print(f"Error extracting entities: {e}")
            return [], []

    def _parse_entities(
        self,
        llm_response: str,
        document_id: int,
        db: Session
    ) -> List[Entity]:
        """Parse entities from LLM response."""
        entities = []
        entity_section = False

        for line in llm_response.split('\n'):
            line = line.strip()

            if 'ENTITIES:' in line.upper():
                entity_section = True
                continue
            elif 'RELATIONSHIPS:' in line.upper():
                entity_section = False
                continue

            if entity_section and line.startswith('-'):
                # Parse format: - [TYPE] Name: Description
                match = re.match(r'-\s*\[([^\]]+)\]\s*([^:]+):\s*(.+)', line)
                if match:
                    entity_type = match.group(1).strip()
                    name = match.group(2).strip()
                    description = match.group(3).strip()

                    # Check if entity already exists
                    existing = db.query(Entity).filter(
                        Entity.document_id == document_id,
                        Entity.name == name,
                        Entity.entity_type == entity_type
                    ).first()

                    if not existing:
                        entity = Entity(
                            name=name,
                            entity_type=entity_type,
                            description=description,
                            document_id=document_id
                        )
                        db.add(entity)
                        entities.append(entity)
                    else:
                        entities.append(existing)

        db.commit()
        for entity in entities:
            db.refresh(entity)

            # Also store in Neo4j if available
            if neo4j_service.is_available():
                # Get user_id from document
                document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
                if document:
                    neo4j_service.create_entity(
                        entity_id=entity.id,
                        name=entity.name,
                        entity_type=entity.entity_type,
                        description=entity.description,
                        document_id=document_id,
                        user_id=document.user_id
                    )

        return entities

    def _parse_relationships(
        self,
        llm_response: str,
        entities: List[Entity],
        db: Session
    ) -> List[Relationship]:
        """Parse relationships from LLM response."""
        relationships = []
        relationship_section = False

        # Create entity lookup
        entity_lookup = {entity.name.lower(): entity for entity in entities}

        for line in llm_response.split('\n'):
            line = line.strip()

            if 'RELATIONSHIPS:' in line.upper():
                relationship_section = True
                continue

            if relationship_section and line.startswith('-'):
                # Parse format: - Source -> Type -> Target: Description
                match = re.match(r'-\s*([^-]+)\s*->\s*([^-]+)\s*->\s*([^:]+):\s*(.+)', line)
                if match:
                    source_name = match.group(1).strip().lower()
                    rel_type = match.group(2).strip()
                    target_name = match.group(3).strip().lower()
                    description = match.group(4).strip()

                    source_entity = entity_lookup.get(source_name)
                    target_entity = entity_lookup.get(target_name)

                    if source_entity and target_entity:
                        relationship = Relationship(
                            relationship_type=rel_type,
                            description=description,
                            source_entity_id=source_entity.id,
                            target_entity_id=target_entity.id
                        )
                        db.add(relationship)
                        relationships.append(relationship)

        db.commit()
        for rel in relationships:
            db.refresh(rel)

            # Also store in Neo4j if available
            if neo4j_service.is_available():
                neo4j_service.create_relationship(
                    relationship_id=rel.id,
                    source_entity_id=rel.source_entity_id,
                    target_entity_id=rel.target_entity_id,
                    relationship_type=rel.relationship_type,
                    description=rel.description
                )

        return relationships

    async def process_document_for_graph(
        self,
        document_id: int,
        chunks: List[Document],
        db: Session
    ) -> None:
        """
        Process document to extract graph knowledge.

        Args:
            document_id: Document ID
            chunks: Document chunks
            db: Database session
        """
        # Combine chunks for entity extraction (limit to avoid token limits)
        combined_text = "\n\n".join([chunk.page_content for chunk in chunks[:10]])

        # Extract entities and relationships
        self.extract_entities_and_relationships(combined_text, document_id, db)

    def get_document_graph(
        self,
        document_id: int,
        db: Session
    ) -> GraphResponse:
        """
        Get graph representation of a document.

        Args:
            document_id: Document ID
            db: Database session

        Returns:
            Graph with nodes and edges
        """
        # Use Neo4j if available for better performance
        if neo4j_service.is_available():
            return neo4j_service.get_document_graph(document_id)

        # Fallback to SQL-based graph storage
        entities = db.query(Entity).filter(Entity.document_id == document_id).all()

        nodes = [
            GraphNode(
                id=entity.id,
                name=entity.name,
                type=entity.entity_type,
                description=entity.description
            )
            for entity in entities
        ]

        # Get all relationships for these entities
        entity_ids = [e.id for e in entities]
        relationships = db.query(Relationship).filter(
            Relationship.source_entity_id.in_(entity_ids)
        ).all()

        edges = [
            GraphEdge(
                source=rel.source_entity_id,
                target=rel.target_entity_id,
                type=rel.relationship_type,
                description=rel.description
            )
            for rel in relationships
        ]

        return GraphResponse(nodes=nodes, edges=edges)

    def get_user_graph(
        self,
        user_id: int,
        db: Session,
        document_ids: Optional[List[int]] = None
    ) -> GraphResponse:
        """
        Get combined graph for user's documents.

        Args:
            user_id: User ID
            db: Database session
            document_ids: Optional list of specific document IDs

        Returns:
            Combined graph
        """
        # Use Neo4j if available for better performance
        if neo4j_service.is_available():
            return neo4j_service.get_user_graph(user_id, document_ids)

        # Fallback to SQL-based graph storage
        query = db.query(Entity).join(DBDocument).filter(DBDocument.user_id == user_id)

        if document_ids:
            query = query.filter(Entity.document_id.in_(document_ids))

        entities = query.all()

        nodes = [
            GraphNode(
                id=entity.id,
                name=entity.name,
                type=entity.entity_type,
                description=entity.description
            )
            for entity in entities
        ]

        entity_ids = [e.id for e in entities]
        relationships = db.query(Relationship).filter(
            Relationship.source_entity_id.in_(entity_ids)
        ).all()

        edges = [
            GraphEdge(
                source=rel.source_entity_id,
                target=rel.target_entity_id,
                type=rel.relationship_type,
                description=rel.description
            )
            for rel in relationships
        ]

        return GraphResponse(nodes=nodes, edges=edges)

    def find_related_entities(
        self,
        entity_name: str,
        db: Session,
        max_depth: int = 2
    ) -> List[Entity]:
        """
        Find entities related to a given entity.

        Args:
            entity_name: Name of the entity
            db: Database session
            max_depth: Maximum relationship depth

        Returns:
            List of related entities
        """
        # Find the initial entity
        entity = db.query(Entity).filter(Entity.name.ilike(f"%{entity_name}%")).first()
        if not entity:
            return []

        related_entities = {entity.id: entity}
        current_level = [entity.id]

        for _ in range(max_depth):
            # Find relationships
            relationships = db.query(Relationship).filter(
                (Relationship.source_entity_id.in_(current_level)) |
                (Relationship.target_entity_id.in_(current_level))
            ).all()

            next_level = []
            for rel in relationships:
                for entity_id in [rel.source_entity_id, rel.target_entity_id]:
                    if entity_id not in related_entities:
                        ent = db.query(Entity).filter(Entity.id == entity_id).first()
                        if ent:
                            related_entities[entity_id] = ent
                            next_level.append(entity_id)

            if not next_level:
                break

            current_level = next_level

        return list(related_entities.values())
