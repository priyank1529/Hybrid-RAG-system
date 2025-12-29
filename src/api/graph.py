from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User
from src.schemas import GraphResponse
from src.auth import get_current_active_user
from src.services.graph_rag import GraphRAGService

router = APIRouter(prefix="/api/graph", tags=["Graph"])
graph_service = GraphRAGService()


@router.get("/document/{document_id}", response_model=GraphResponse)
async def get_document_graph(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get graph visualization for a specific document."""
    # Verify document belongs to user
    from src.models import Document as DBDocument
    document = db.query(DBDocument).filter(
        DBDocument.id == document_id,
        DBDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        graph = graph_service.get_document_graph(document_id, db)
        return graph
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving graph: {str(e)}"
        )


@router.get("/user", response_model=GraphResponse)
async def get_user_graph(
    document_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get combined graph for user's documents.

    Args:
        document_ids: Optional list of document IDs to filter
        db: Database session
        current_user: Authenticated user

    Returns:
        Combined graph with all entities and relationships
    """
    try:
        graph = graph_service.get_user_graph(
            user_id=current_user.id,
            db=db,
            document_ids=document_ids
        )
        return graph
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving graph: {str(e)}"
        )
