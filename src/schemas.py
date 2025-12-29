from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Document Schemas
class DocumentBase(BaseModel):
    filename: str
    file_type: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: Optional[int]
    collection_name: str
    chunk_count: int
    status: str
    error_message: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]
    user_id: int

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    total: int
    documents: List[DocumentResponse]


# Entity Schemas
class EntityBase(BaseModel):
    name: str
    entity_type: str
    description: Optional[str] = None


class EntityCreate(EntityBase):
    document_id: int


class EntityResponse(EntityBase):
    id: int
    document_id: int

    class Config:
        from_attributes = True


# Relationship Schemas
class RelationshipBase(BaseModel):
    relationship_type: str
    description: Optional[str] = None


class RelationshipCreate(RelationshipBase):
    source_entity_id: int
    target_entity_id: int


class RelationshipResponse(RelationshipBase):
    id: int
    source_entity_id: int
    target_entity_id: int

    class Config:
        from_attributes = True


# Graph Schemas
class GraphNode(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str] = None


class GraphEdge(BaseModel):
    source: int
    target: int
    type: str
    description: Optional[str] = None


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# RAG Query Schemas
class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    use_graph: bool = Field(default=True, description="Whether to use graph-based retrieval")
    document_ids: Optional[List[int]] = Field(default=None, description="Filter by specific documents")


class RetrievedChunk(BaseModel):
    content: str
    score: float
    document_id: Optional[int] = None
    metadata: dict = {}


class QueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    entities_found: List[EntityResponse] = []
    graph_context: Optional[GraphResponse] = None
