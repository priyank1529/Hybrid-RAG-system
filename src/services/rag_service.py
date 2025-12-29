from typing import List, Optional
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document

from src.config import get_settings
from src.embeddings import embeddings
from src.vectorstore.qdrant import get_vectorstore
from src.models import Document as DBDocument, Entity, User
from src.schemas import QueryResponse, RetrievedChunk, EntityResponse, GraphResponse
from src.services.graph_rag import GraphRAGService

settings = get_settings()


class RAGService:
    """Service for RAG queries with graph enhancement."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.google_api_key,
            temperature=0.7
        )
        self.graph_service = GraphRAGService()

    async def query(
        self,
        query_text: str,
        user: User,
        db: Session,
        top_k: int = 5,
        use_graph: bool = True,
        document_ids: Optional[List[int]] = None
    ) -> QueryResponse:
        """
        Query user's documents with optional graph enhancement.

        Args:
            query_text: User's query
            user: Current user
            db: Database session
            top_k: Number of chunks to retrieve
            use_graph: Whether to use graph-based retrieval
            document_ids: Optional filter for specific documents

        Returns:
            Query response with answer and context
        """
        # Get user's documents
        query_docs = db.query(DBDocument).filter(
            DBDocument.user_id == user.id,
            DBDocument.status == "completed"
        )

        if document_ids:
            query_docs = query_docs.filter(DBDocument.id.in_(document_ids))

        documents = query_docs.all()

        if not documents:
            return QueryResponse(
                query=query_text,
                answer="No documents found. Please upload documents first.",
                retrieved_chunks=[],
                entities_found=[],
                graph_context=None
            )

        # Retrieve chunks from vector store
        all_chunks = []
        for doc in documents:
            try:
                vectorstore = get_vectorstore(embeddings, doc.collection_name)
                results = vectorstore.similarity_search_with_score(query_text, k=top_k)

                for content, score in results:
                    all_chunks.append({
                        "content": content.page_content,
                        "score": float(score),
                        "document_id": doc.id,
                        "metadata": content.metadata
                    })
            except Exception as e:
                print(f"Error retrieving from {doc.collection_name}: {e}")
                continue

        # Sort by score and take top_k
        all_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_chunks = all_chunks[:top_k]

        retrieved_chunks = [
            RetrievedChunk(
                content=chunk["content"],
                score=chunk["score"],
                document_id=chunk["document_id"],
                metadata=chunk.get("metadata", {})
            )
            for chunk in top_chunks
        ]

        # Graph-enhanced retrieval
        entities_found = []
        graph_context = None

        if use_graph:
            # Find entities related to query
            entities = self._find_query_entities(query_text, user.id, db, document_ids)
            entities_found = [
                EntityResponse(
                    id=e.id,
                    name=e.name,
                    entity_type=e.entity_type,
                    description=e.description,
                    document_id=e.document_id
                )
                for e in entities
            ]

            # Get graph context
            if entities:
                graph_context = self.graph_service.get_user_graph(
                    user.id,
                    db,
                    document_ids
                )

        # Generate answer using LLM
        answer = await self._generate_answer(
            query_text,
            retrieved_chunks,
            entities_found,
            graph_context
        )

        return QueryResponse(
            query=query_text,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            entities_found=entities_found,
            graph_context=graph_context
        )

    def _find_query_entities(
        self,
        query: str,
        user_id: int,
        db: Session,
        document_ids: Optional[List[int]] = None
    ) -> List[Entity]:
        """Find entities relevant to the query."""
        # Search for entities by name matching query keywords
        query_words = query.lower().split()

        query_entities = db.query(Entity).join(DBDocument).filter(
            DBDocument.user_id == user_id
        )

        if document_ids:
            query_entities = query_entities.filter(Entity.document_id.in_(document_ids))

        entities = query_entities.all()

        # Filter entities that match query keywords
        relevant_entities = []
        for entity in entities:
            entity_text = f"{entity.name} {entity.description or ''}".lower()
            if any(word in entity_text for word in query_words):
                relevant_entities.append(entity)

                # Also add related entities
                related = self.graph_service.find_related_entities(
                    entity.name,
                    db,
                    max_depth=1
                )
                relevant_entities.extend(related)

        # Remove duplicates
        seen = set()
        unique_entities = []
        for entity in relevant_entities:
            if entity.id not in seen:
                seen.add(entity.id)
                unique_entities.append(entity)

        return unique_entities[:10]  # Limit to top 10

    async def _generate_answer(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        entities: List[EntityResponse],
        graph: Optional[GraphResponse]
    ) -> str:
        """Generate answer using LLM with retrieved context."""
        # Build context
        context_parts = []

        if chunks:
            context_parts.append("Retrieved Information:")
            for i, chunk in enumerate(chunks, 1):
                context_parts.append(f"\n[{i}] {chunk.content}")

        if entities:
            context_parts.append("\n\nRelevant Entities:")
            for entity in entities:
                desc = f" - {entity.description}" if entity.description else ""
                context_parts.append(f"- {entity.name} ({entity.entity_type}){desc}")

        if graph and graph.edges:
            context_parts.append("\n\nRelationships:")
            for edge in graph.edges[:5]:  # Limit to 5 relationships
                # Find entity names from graph nodes
                source_node = next((n for n in graph.nodes if n.id == edge.source), None)
                target_node = next((n for n in graph.nodes if n.id == edge.target), None)
                if source_node and target_node:
                    context_parts.append(
                        f"- {source_node.name} {edge.type} {target_node.name}"
                    )

        context = "\n".join(context_parts)

        prompt = f"""Answer the following question based on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, concise answer based on the context
- If the context doesn't contain enough information, say so
- Use specific details from the context when available
- Reference entities and relationships when relevant

Answer:"""

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"Error generating answer: {str(e)}"
