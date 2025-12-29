from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User
from src.schemas import QueryRequest, QueryResponse
from src.auth import get_current_active_user
from src.services.rag_service import RAGService

router = APIRouter(prefix="/api/query", tags=["Query"])
rag_service = RAGService()


@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Query user's documents using RAG with optional graph enhancement.

    Args:
        request: Query request with parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        Query response with answer and context
    """
    try:
        response = await rag_service.query(
            query_text=request.query,
            user=current_user,
            db=db,
            top_k=request.top_k,
            use_graph=request.use_graph,
            document_ids=request.document_ids
        )
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )
