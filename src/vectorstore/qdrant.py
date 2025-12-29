from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from typing import List
from langchain.schema import Document
from src.config import get_settings

settings = get_settings()


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )


def store_in_qdrant(
    docs: List[Document],
    embeddings,
    collection_name: str
) -> QdrantVectorStore:
    """
    Store documents in Qdrant with user-specific collection.

    Args:
        docs: List of documents to store
        embeddings: Embedding model to use
        collection_name: Name of the collection (user-specific)

    Returns:
        QdrantVectorStore instance
    """
    vectorstore = QdrantVectorStore.from_documents(
        docs,
        embeddings,
        prefer_grpc=True,
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=collection_name
    )
    return vectorstore


def get_vectorstore(
    embeddings,
    collection_name: str
) -> QdrantVectorStore:
    """
    Get existing Qdrant vector store for querying.

    Args:
        embeddings: Embedding model to use
        collection_name: Name of the collection (user-specific)

    Returns:
        QdrantVectorStore instance
    """
    vectorstore = QdrantVectorStore(
        client=get_qdrant_client(),
        embedding=embeddings,
        collection_name=collection_name
    )
    return vectorstore


