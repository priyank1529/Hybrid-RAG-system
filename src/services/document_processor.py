import os
import re
import mimetypes
import filetype
from typing import List, Tuple
from datetime import datetime
from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    JSONLoader,
    PyMuPDFLoader,
    WebBaseLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sqlalchemy.orm import Session

from src.config import get_settings
from src.embeddings import embeddings
from src.vectorstore.qdrant import store_in_qdrant
from src.models import Document as DBDocument
from src.models import User

settings = get_settings()


def is_url(path: str) -> bool:
    """Detect if path is a URL."""
    return bool(re.match(r'^https?://', path.strip(), re.IGNORECASE))


def detect_file_type(file_path: str) -> Tuple[str, str]:
    """
    Detect file type from path.

    Returns:
        Tuple of (extension, mime_type)
    """
    if is_url(file_path):
        return "url", "text/html"

    ext = os.path.splitext(file_path)[1].lower()
    mime, _ = mimetypes.guess_type(file_path)
    kind = filetype.guess(file_path)

    if kind:
        return kind.extension, kind.mime

    return ext.replace(".", ""), mime


def load_file(file_path: str) -> List[Document]:
    """
    Load file based on its type.

    Args:
        file_path: Path to file or URL

    Returns:
        List of loaded documents
    """
    ext, mime = detect_file_type(file_path)

    if ext == "url" and mime == "text/html":
        loader = WebBaseLoader(file_path)
    elif ext in ["text", "txt"] and mime == "text/plain":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext in ["csv"] or mime == "text/csv":
        loader = CSVLoader(file_path=file_path)
    elif ext in ["json"] or mime == "application/json":
        loader = JSONLoader(file_path)
    elif ext in ["pdf"] or mime == "application/pdf":
        loader = PyMuPDFLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext} / {mime}")

    return loader.load()


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into chunks.

    Args:
        documents: List of documents to split

    Returns:
        List of chunked documents
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    return text_splitter.split_documents(documents)


def get_user_collection_name(user_id: int, document_id: int) -> str:
    """
    Generate collection name for user's document.

    Args:
        user_id: User ID
        document_id: Document ID

    Returns:
        Collection name
    """
    return f"user_{user_id}_doc_{document_id}"


async def process_document(
    file_path: str,
    original_filename: str,
    user: User,
    db: Session
) -> DBDocument:
    """
    Process and store a document with metadata.

    Args:
        file_path: Path to the uploaded file
        original_filename: Original name of the file
        user: User who uploaded the document
        db: Database session

    Returns:
        Document database record
    """
    try:
        # Detect file type and size
        ext, mime = detect_file_type(file_path)
        file_size = os.path.getsize(file_path) if not is_url(file_path) else None

        # Create document record
        db_document = DBDocument(
            filename=os.path.basename(file_path),
            original_filename=original_filename,
            file_type=ext,
            file_size=file_size,
            file_path=file_path,
            collection_name="",  # Will be set after ID is generated
            status="processing",
            user_id=user.id
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Generate collection name with document ID
        collection_name = get_user_collection_name(user.id, db_document.id)
        db_document.collection_name = collection_name
        db.commit()

        # Load and process document
        documents = load_file(file_path)

        # Add metadata to documents
        for doc in documents:
            doc.metadata.update({
                "user_id": user.id,
                "document_id": db_document.id,
                "filename": original_filename,
                "file_type": ext
            })

        # Split into chunks
        chunks = split_documents(documents)

        # Store in Qdrant
        store_in_qdrant(chunks, embeddings, collection_name)

        # Update document record
        db_document.chunk_count = len(chunks)
        db_document.status = "completed"
        db_document.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_document)

        return db_document

    except Exception as e:
        # Update document with error
        if db_document:
            db_document.status = "failed"
            db_document.error_message = str(e)
            db.commit()
        raise e
