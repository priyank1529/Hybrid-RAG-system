"""
Graph RAG Application - Main Entry Point

This application provides a multi-user document management system with:
- User authentication
- Document upload and processing
- Graph-based RAG (Retrieval Augmented Generation)
- Entity extraction and relationship mapping
- Vector-based semantic search
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import engine, Base
from src.api.auth import router as auth_router
from src.api.documents import router as documents_router
from src.api.query import router as query_router
from src.api.graph import router as graph_router
from src.api.resume import router as resume_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Graph RAG API",
    description="Multi-user document management with Graph-based RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(graph_router)
app.include_router(resume_router)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Graph RAG API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/auth",
            "documents": "/api/documents",
            "query": "/api/query",
            "graph": "/api/graph",
            "resume": "/api/resume"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
