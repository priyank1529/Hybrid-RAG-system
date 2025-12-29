import os
import shutil
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, Document as DBDocument
from src.schemas import DocumentResponse, DocumentList
from src.auth import get_current_active_user
from src.services.document_processor import process_document
from src.services.graph_rag import GraphRAGService
from src.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/documents", tags=["Documents"])
graph_service = GraphRAGService()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a document for processing."""
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_dir) / f"user_{current_user.id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    file_path = upload_dir / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

    # Process document
    try:
        document = await process_document(
            str(file_path),
            file.filename,
            current_user,
            db
        )

        # Extract entities and relationships for Graph RAG
        from src.services.document_processor import load_file, split_documents
        docs = load_file(str(file_path))
        chunks = split_documents(docs)

        await graph_service.process_document_for_graph(document.id, chunks, db)

        return document

    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all documents for the current user."""
    documents = db.query(DBDocument).filter(
        DBDocument.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    total = db.query(DBDocument).filter(
        DBDocument.user_id == current_user.id
    ).count()

    return DocumentList(total=total, documents=documents)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific document."""
    document = db.query(DBDocument).filter(
        DBDocument.id == document_id,
        DBDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a document and its associated data."""
    document = db.query(DBDocument).filter(
        DBDocument.id == document_id,
        DBDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete physical file
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    # Delete from Qdrant
    try:
        from src.vectorstore.qdrant import get_qdrant_client
        client = get_qdrant_client()
        client.delete_collection(document.collection_name)
    except Exception as e:
        print(f"Error deleting Qdrant collection: {e}")

    # Delete from Neo4j if available
    try:
        from src.graphdb.neo4j_service import neo4j_service
        if neo4j_service.is_available():
            neo4j_service.delete_document_graph(document_id)
    except Exception as e:
        print(f"Error deleting from Neo4j: {e}")

    # Delete from database (entities and relationships will cascade)
    db.delete(document)
    db.commit()

    return None
