# Graph RAG System - Complete Technical Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Data Flow](#data-flow)
5. [Component Details](#component-details)
6. [API Specifications](#api-specifications)
7. [Database Schema](#database-schema)
8. [Security Implementation](#security-implementation)
9. [Deployment Guide](#deployment-guide)
10. [Performance Optimization](#performance-optimization)

---

## System Overview

### What is Graph RAG?

**Graph RAG** combines three powerful technologies:

1. **RAG (Retrieval Augmented Generation)** - Retrieve relevant context before generating answers
2. **Knowledge Graphs** - Store entities and relationships as graph structures
3. **Vector Search** - Semantic similarity search using embeddings

### Core Functionality

```
User Query → Vector Search (Qdrant) → Retrieved Chunks
                    ↓
            Entity Detection
                    ↓
         Relationship Traversal (Neo4j/SQL)
                    ↓
            Enriched Context
                    ↓
        LLM Answer Generation (Gemini)
                    ↓
            Response to User
```

### Key Features

- **Multi-tenant**: Each user has isolated documents and graphs
- **Flexible Storage**: Choose between SQL or Neo4j for graph storage
- **Scalable**: Designed to handle thousands of documents per user
- **Secure**: JWT authentication, password hashing, per-user isolation

---

## Technology Stack

### Backend Framework

**FastAPI 0.119+**
- **Why**: Modern, fast (high-performance), automatic API docs
- **Features Used**:
  - Dependency injection for auth
  - Pydantic models for validation
  - Automatic OpenAPI/Swagger docs
  - Async support for better concurrency
  - Type hints for better IDE support

```python
# Example FastAPI endpoint
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Process file
    return document
```

### Web Server

**Uvicorn 0.27+**
- **Why**: ASGI server for async Python applications
- **Features**: Fast, lightweight, production-ready
- **Usage**: `uvicorn.run("main:app", host="0.0.0.0", port=8000)`

### Language Models

**1. Google Gemini**

- **Embeddings**: `gemini-embedding-001` (768 dimensions)
  - Converts text to vector representations
  - Used for semantic similarity search
  - Cost-effective and accurate

- **LLM**: `gemini-pro`
  - Entity extraction from documents
  - Relationship identification
  - Answer generation from context
  - Temperature: 0 (deterministic) for entities, 0.7 for answers

```python
# Embedding initialization
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.google_api_key
)

# LLM initialization
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=settings.google_api_key,
    temperature=0.7
)
```

**Why Gemini?**
- Free tier available
- Good quality embeddings
- Fast response times
- Easy API integration

### Vector Database

**Qdrant Cloud 1.15+**
- **Why**: Purpose-built for vector search
- **Features**:
  - Fast similarity search
  - gRPC support for performance
  - Cloud-hosted (no infrastructure needed)
  - Collection per user-document

```python
# Vector storage
vectorstore = QdrantVectorStore.from_documents(
    docs,
    embeddings,
    prefer_grpc=True,
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
    collection_name=f"user_{user_id}_doc_{doc_id}"
)
```

**Data Structure in Qdrant**:
```json
{
  "id": "uuid",
  "vector": [0.123, -0.456, ...],  // 768 dimensions
  "payload": {
    "content": "Document chunk text",
    "user_id": 1,
    "document_id": 5,
    "filename": "research.pdf",
    "file_type": "pdf"
  }
}
```

### Graph Databases

**Option 1: SQLite/PostgreSQL (Default)**

- **SQLAlchemy 2.0+**: ORM for database operations
- **Why SQL for graphs?**:
  - Zero additional setup
  - Good for small-medium graphs
  - Familiar technology

**Schema**:
```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    entity_type VARCHAR NOT NULL,
    description TEXT,
    document_id INTEGER REFERENCES documents(id)
);

CREATE TABLE relationships (
    id INTEGER PRIMARY KEY,
    source_entity_id INTEGER REFERENCES entities(id),
    target_entity_id INTEGER REFERENCES entities(id),
    relationship_type VARCHAR NOT NULL,
    description TEXT
);
```

**Option 2: Neo4j 5.14+ (Optional)**

- **neo4j-driver**: Python driver for Neo4j
- **Why Neo4j?**:
  - Native graph database
  - 5-10x faster for complex queries
  - Visual graph browser
  - Advanced graph algorithms

**Schema**:
```cypher
(:Entity {
    id: Integer,
    name: String,
    type: String,
    description: String,
    document_id: Integer,
    user_id: Integer
})

-[:RELATED {
    id: Integer,
    type: String,
    description: String
}]->

(:Entity)
```

### Authentication & Security

**1. JWT Tokens**
- **Library**: python-jose[cryptography] 3.3+
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 30 minutes (configurable)

```python
# Token generation
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm="HS256"
    )
    return encoded_jwt
```

**2. Password Hashing**
- **Library**: passlib[bcrypt] 1.7+
- **Algorithm**: bcrypt (adaptive hash function)
- **Rounds**: 12 (default)

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("user_password")

# Verify password
is_valid = pwd_context.verify("user_password", hashed)
```

### Document Processing

**LangChain 1.0+**
- **Why**: Unified interface for document loading and processing
- **Loaders Used**:
  - `TextLoader`: Plain text files
  - `CSVLoader`: CSV files
  - `JSONLoader`: JSON documents
  - `PyMuPDFLoader`: PDF files (using pymupdf)
  - `WebBaseLoader`: Web URLs

```python
# Document loading example
if file_type == "pdf":
    loader = PyMuPDFLoader(file_path)
elif file_type == "csv":
    loader = CSVLoader(file_path)
# ... etc

documents = loader.load()
```

**Text Splitting**:
- **RecursiveCharacterTextSplitter**:
  - Chunk size: 500 characters
  - Chunk overlap: 50 characters
  - Preserves semantic meaning
  - Handles multiple document types

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
    is_separator_regex=False
)
chunks = text_splitter.split_documents(documents)
```

### Data Validation

**Pydantic 2.0+**
- **Why**: Data validation using Python type hints
- **Features**:
  - Automatic validation
  - JSON schema generation
  - Clear error messages
  - IDE autocomplete support

```python
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str
    chunk_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy models
```

### Configuration Management

**pydantic-settings 2.0+**
- **Why**: Type-safe configuration from environment variables
- **Features**:
  - Automatic .env file loading
  - Type validation
  - Default values
  - Case-insensitive keys

```python
class Settings(BaseSettings):
    qdrant_url: str
    qdrant_api_key: str
    google_api_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

## Architecture Deep Dive

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                │
│  - FastAPI Routes                           │
│  - Request/Response Models                  │
│  - Authentication Middleware                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          Business Logic Layer               │
│  - DocumentProcessor Service                │
│  - GraphRAG Service                         │
│  - RAG Query Service                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│           Data Access Layer                 │
│  - SQLAlchemy Models                        │
│  - Qdrant Client                            │
│  - Neo4j Driver                             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│            Storage Layer                    │
│  - SQLite/PostgreSQL (metadata)             │
│  - Qdrant (vectors)                         │
│  - Neo4j (graph - optional)                 │
│  - File System (documents)                  │
└─────────────────────────────────────────────┘
```

### Directory Structure

```
graph-rag/
│
├── main.py                          # Application entry point
│
├── src/
│   ├── config.py                    # Configuration settings
│   ├── database.py                  # Database session management
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── schemas.py                   # Pydantic request/response models
│   ├── auth.py                      # JWT authentication logic
│   ├── embeddings.py                # Embedding model initialization
│   │
│   ├── api/                         # API route handlers
│   │   ├── auth.py                  # User registration, login
│   │   ├── documents.py             # Document CRUD operations
│   │   ├── query.py                 # RAG query endpoint
│   │   └── graph.py                 # Graph visualization endpoints
│   │
│   ├── services/                    # Business logic
│   │   ├── document_processor.py    # File loading, chunking, storage
│   │   ├── graph_rag.py             # Entity extraction, relationships
│   │   └── rag_service.py           # Query processing, answer generation
│   │
│   ├── graphdb/                     # Graph database integrations
│   │   └── neo4j_service.py         # Neo4j operations
│   │
│   └── vectorstore/                 # Vector database
│       └── qdrant.py                # Qdrant operations
│
├── uploads/                         # User-uploaded files
│   └── user_{id}/                   # Per-user directories
│
└── graph_rag.db                     # SQLite database
```

---

## Data Flow

### 1. Document Upload Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. CLIENT REQUEST                                            │
│    POST /api/documents/upload                                │
│    - multipart/form-data with file                           │
│    - Authorization: Bearer <token>                           │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. AUTHENTICATION                                            │
│    - Verify JWT token                                        │
│    - Extract user from token                                 │
│    - Check user is active                                    │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. FILE STORAGE                                              │
│    - Save to: uploads/user_{id}/{filename}                   │
│    - Detect file type (PDF, CSV, JSON, TXT)                  │
│    - Record file size                                        │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. CREATE DATABASE RECORD                                    │
│    INSERT INTO documents (                                   │
│        filename, file_type, file_size,                       │
│        user_id, status='processing'                          │
│    )                                                         │
│    RETURNING id;                                             │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. DOCUMENT LOADING                                          │
│    - Use appropriate loader (PDF/CSV/JSON/TXT)               │
│    - Extract text content                                    │
│    - Handle encoding (UTF-8)                                 │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. TEXT CHUNKING                                             │
│    RecursiveCharacterTextSplitter:                           │
│    - chunk_size: 500                                         │
│    - chunk_overlap: 50                                       │
│    - Preserve context across chunks                          │
│    Result: List of Document objects                          │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. ADD METADATA                                              │
│    For each chunk:                                           │
│    chunk.metadata = {                                        │
│        "user_id": 1,                                         │
│        "document_id": 5,                                     │
│        "filename": "research.pdf",                           │
│        "file_type": "pdf"                                    │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 8. GENERATE EMBEDDINGS                                       │
│    For each chunk:                                           │
│    - Send text to Gemini API                                 │
│    - Receive 768-dim vector                                  │
│    - Batch processing for efficiency                         │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 9. STORE IN QDRANT                                           │
│    Collection: user_1_doc_5                                  │
│    For each chunk:                                           │
│    {                                                         │
│        "vector": [0.123, ...],                               │
│        "payload": {                                          │
│            "content": "chunk text",                          │
│            "metadata": {...}                                 │
│        }                                                     │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 10. ENTITY EXTRACTION (Graph RAG)                            │
│     - Combine first 10 chunks                                │
│     - Send to Gemini for entity extraction                   │
│     - Parse response for entities & relationships            │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 11. STORE ENTITIES                                           │
│     SQL: INSERT INTO entities (name, type, description)      │
│     Neo4j (if enabled): CREATE (:Entity {...})               │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 12. STORE RELATIONSHIPS                                      │
│     SQL: INSERT INTO relationships (source, target, type)    │
│     Neo4j (if enabled): CREATE ()-[:RELATED]->()             │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 13. UPDATE DOCUMENT STATUS                                   │
│     UPDATE documents SET                                     │
│         status = 'completed',                                │
│         chunk_count = 42,                                    │
│         processed_at = NOW()                                 │
│     WHERE id = 5;                                            │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 14. RETURN RESPONSE                                          │
│     {                                                        │
│         "id": 5,                                             │
│         "filename": "research.pdf",                          │
│         "status": "completed",                               │
│         "chunk_count": 42                                    │
│     }                                                        │
└──────────────────────────────────────────────────────────────┘
```

### 2. RAG Query Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. CLIENT REQUEST                                            │
│    POST /api/query/                                          │
│    {                                                         │
│        "query": "What is machine learning?",                 │
│        "top_k": 5,                                           │
│        "use_graph": true                                     │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. AUTHENTICATION                                            │
│    - Verify JWT token                                        │
│    - Get current user                                        │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. GET USER'S DOCUMENTS                                      │
│    SELECT * FROM documents                                   │
│    WHERE user_id = 1                                         │
│      AND status = 'completed';                               │
│    Result: [doc1, doc2, doc3]                                │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. EMBED QUERY                                               │
│    query_vector = embeddings.embed_query(                    │
│        "What is machine learning?"                           │
│    )                                                         │
│    Result: [0.456, -0.123, ...] (768 dims)                   │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. VECTOR SIMILARITY SEARCH                                  │
│    For each document collection:                             │
│        results = qdrant.search(                              │
│            collection="user_1_doc_1",                        │
│            query_vector=query_vector,                        │
│            limit=5                                           │
│        )                                                     │
│    Aggregate and sort by score                               │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. RETRIEVED CHUNKS                                          │
│    [                                                         │
│        {                                                     │
│            "content": "ML is a subset of AI...",             │
│            "score": 0.89,                                    │
│            "document_id": 1                                  │
│        },                                                    │
│        ...                                                   │
│    ]                                                         │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. ENTITY DETECTION (if use_graph=true)                      │
│    - Extract keywords from query: ["machine learning"]       │
│    - Search entities:                                        │
│      SELECT * FROM entities                                  │
│      WHERE name LIKE '%machine learning%'                    │
│        AND document_id IN (user_documents);                  │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 8. RELATIONSHIP TRAVERSAL                                    │
│    SQL: Multi-hop JOIN query                                 │
│    Neo4j: MATCH (e)-[:RELATED*1..2]-(related)                │
│    Result: Related entities and relationships                │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 9. BUILD CONTEXT                                             │
│    context = {                                               │
│        "chunks": [...],                                      │
│        "entities": [                                         │
│            {"name": "Machine Learning", "type": "CONCEPT"},  │
│            {"name": "Neural Networks", "type": "TECHNOLOGY"} │
│        ],                                                    │
│        "relationships": [                                    │
│            "Machine Learning uses Neural Networks"           │
│        ]                                                     │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 10. GENERATE PROMPT                                          │
│     prompt = f"""                                            │
│     Context:                                                 │
│     {chunks}                                                 │
│                                                              │
│     Entities: {entities}                                     │
│     Relationships: {relationships}                           │
│                                                              │
│     Question: {query}                                        │
│                                                              │
│     Answer based on context:                                 │
│     """                                                      │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 11. LLM GENERATION                                           │
│     response = llm.invoke(prompt)                            │
│     Result: "Machine learning is a subset..."                │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ 12. RETURN RESPONSE                                          │
│     {                                                        │
│         "query": "What is machine learning?",                │
│         "answer": "Machine learning is...",                  │
│         "retrieved_chunks": [...],                           │
│         "entities_found": [...],                             │
│         "graph_context": {                                   │
│             "nodes": [...],                                  │
│             "edges": [...]                                   │
│         }                                                    │
│     }                                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Authentication System

**File**: `src/auth.py`

**Components**:

```python
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain, hashed)
```

```python
# JWT token creation
def create_access_token(data: dict) -> str:
    """Create JWT token with expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

```python
# Token verification
async def get_current_user(token: str, db: Session) -> User:
    """Extract and verify user from token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(401, "Invalid credentials")
        return user
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

**Security Features**:
- Passwords never stored in plain text
- Bcrypt with 12 rounds (adaptive)
- JWT tokens expire after 30 minutes
- Token verification on every protected endpoint
- Per-user data isolation

### 2. Document Processor

**File**: `src/services/document_processor.py`

**Key Functions**:

```python
def detect_file_type(file_path: str) -> Tuple[str, str]:
    """
    Detect file type using multiple methods:
    1. Check if URL
    2. Check file extension
    3. Use mimetypes library
    4. Use filetype library (magic numbers)
    """
    if is_url(file_path):
        return "url", "text/html"

    # Extension-based
    ext = os.path.splitext(file_path)[1].lower()

    # MIME type
    mime, _ = mimetypes.guess_type(file_path)

    # Magic numbers
    kind = filetype.guess(file_path)
    if kind:
        return kind.extension, kind.mime

    return ext.replace(".", ""), mime
```

```python
def load_file(file_path: str) -> List[Document]:
    """Load file using appropriate loader"""
    ext, mime = detect_file_type(file_path)

    loaders = {
        ("url", "text/html"): WebBaseLoader,
        ("txt", "text/plain"): lambda p: TextLoader(p, encoding="utf-8"),
        ("csv", "text/csv"): CSVLoader,
        ("json", "application/json"): JSONLoader,
        ("pdf", "application/pdf"): PyMuPDFLoader
    }

    loader_class = loaders.get((ext, mime))
    if not loader_class:
        raise ValueError(f"Unsupported file type: {ext}/{mime}")

    loader = loader_class(file_path)
    return loader.load()
```

```python
def split_documents(documents: List[Document]) -> List[Document]:
    """Split documents into chunks"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # Characters per chunk
        chunk_overlap=50,    # Overlap for context
        length_function=len,
        is_separator_regex=False
    )
    return splitter.split_documents(documents)
```

**Processing Steps**:
1. File type detection (extension + MIME + magic numbers)
2. Appropriate loader selection
3. Text extraction
4. Chunking with overlap
5. Metadata addition
6. Embedding generation
7. Vector storage
8. Entity extraction

### 3. Graph RAG Service

**File**: `src/services/graph_rag.py`

**Entity Extraction**:

```python
def extract_entities_and_relationships(
    self,
    text: str,
    document_id: int,
    db: Session
) -> Tuple[List[Entity], List[Relationship]]:
    """Extract entities and relationships using LLM"""

    # Prompt for LLM
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
"""

    # Call LLM
    response = self.llm.invoke(prompt)

    # Parse response
    entities = self._parse_entities(response.content, document_id, db)
    relationships = self._parse_relationships(response.content, entities, db)

    return entities, relationships
```

**Parsing Logic**:

```python
def _parse_entities(self, llm_response: str, document_id: int, db: Session):
    """Parse entities from LLM response"""
    entities = []

    # Find ENTITIES section
    for line in llm_response.split('\n'):
        if line.startswith('-') and '[' in line:
            # Parse: - [TYPE] Name: Description
            match = re.match(r'-\s*\[([^\]]+)\]\s*([^:]+):\s*(.+)', line)
            if match:
                entity_type = match.group(1).strip()
                name = match.group(2).strip()
                description = match.group(3).strip()

                # Create entity
                entity = Entity(
                    name=name,
                    entity_type=entity_type,
                    description=description,
                    document_id=document_id
                )
                db.add(entity)
                entities.append(entity)

    db.commit()

    # Also store in Neo4j if available
    if neo4j_service.is_available():
        for entity in entities:
            neo4j_service.create_entity(
                entity_id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
                document_id=document_id,
                user_id=document.user_id
            )

    return entities
```

### 4. RAG Query Service

**File**: `src/services/rag_service.py`

**Query Processing**:

```python
async def query(
    self,
    query_text: str,
    user: User,
    db: Session,
    top_k: int = 5,
    use_graph: bool = True,
    document_ids: Optional[List[int]] = None
) -> QueryResponse:
    """Process RAG query with graph enhancement"""

    # 1. Get user's documents
    documents = db.query(Document).filter(
        Document.user_id == user.id,
        Document.status == "completed"
    )
    if document_ids:
        documents = documents.filter(Document.id.in_(document_ids))
    documents = documents.all()

    # 2. Retrieve chunks from vector store
    all_chunks = []
    for doc in documents:
        vectorstore = get_vectorstore(embeddings, doc.collection_name)
        results = vectorstore.similarity_search_with_score(query_text, k=top_k)

        for content, score in results:
            all_chunks.append({
                "content": content.page_content,
                "score": float(score),
                "document_id": doc.id,
                "metadata": content.metadata
            })

    # 3. Sort by score and take top_k
    all_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = all_chunks[:top_k]

    # 4. Graph enhancement (if enabled)
    entities_found = []
    graph_context = None

    if use_graph:
        # Find relevant entities
        entities = self._find_query_entities(query_text, user.id, db, document_ids)

        # Get graph context
        if entities:
            graph_context = self.graph_service.get_user_graph(
                user.id, db, document_ids
            )

    # 5. Generate answer
    answer = await self._generate_answer(
        query_text,
        top_chunks,
        entities_found,
        graph_context
    )

    return QueryResponse(
        query=query_text,
        answer=answer,
        retrieved_chunks=top_chunks,
        entities_found=entities_found,
        graph_context=graph_context
    )
```

### 5. Neo4j Service

**File**: `src/graphdb/neo4j_service.py`

**Key Operations**:

```python
def create_entity(
    self,
    entity_id: int,
    name: str,
    entity_type: str,
    description: Optional[str],
    document_id: int,
    user_id: int
):
    """Create entity node in Neo4j"""
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
            description=description,
            document_id=document_id,
            user_id=user_id
        )
```

```python
def find_shortest_path(
    self,
    entity1_name: str,
    entity2_name: str,
    user_id: int
) -> Optional[List[Dict]]:
    """Find shortest path between two entities"""
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
            """,
            user_id=user_id,
            entity1_name=entity1_name,
            entity2_name=entity2_name
        )

        record = result.single()
        return record["path"] if record else None
```

---

## API Specifications

### Authentication Endpoints

**POST /api/auth/register**

Request:
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "SecurePass123"
}
```

Response (201):
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00"
}
```

**POST /api/auth/login**

Request (form-data):
```
username=alice
password=SecurePass123
```

Response (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Document Endpoints

**POST /api/documents/upload**

Request:
```
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <binary data>
```

Response (201):
```json
{
  "id": 5,
  "filename": "research.pdf",
  "original_filename": "research.pdf",
  "file_type": "pdf",
  "file_size": 524288,
  "collection_name": "user_1_doc_5",
  "chunk_count": 42,
  "status": "completed",
  "error_message": null,
  "uploaded_at": "2024-01-01T12:00:00",
  "processed_at": "2024-01-01T12:00:15",
  "user_id": 1
}
```

**GET /api/documents/**

Response (200):
```json
{
  "total": 3,
  "documents": [
    {
      "id": 5,
      "filename": "research.pdf",
      "file_type": "pdf",
      "chunk_count": 42,
      "status": "completed",
      "uploaded_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### Query Endpoint

**POST /api/query/**

Request:
```json
{
  "query": "What is machine learning?",
  "top_k": 5,
  "use_graph": true,
  "document_ids": [1, 2]
}
```

Response (200):
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is a subset of artificial intelligence...",
  "retrieved_chunks": [
    {
      "content": "ML is a branch of AI...",
      "score": 0.89,
      "document_id": 1,
      "metadata": {
        "filename": "research.pdf",
        "file_type": "pdf"
      }
    }
  ],
  "entities_found": [
    {
      "id": 1,
      "name": "Machine Learning",
      "entity_type": "CONCEPT",
      "description": "A method of data analysis",
      "document_id": 1
    }
  ],
  "graph_context": {
    "nodes": [
      {
        "id": 1,
        "name": "Machine Learning",
        "type": "CONCEPT",
        "description": "A method of data analysis"
      }
    ],
    "edges": [
      {
        "source": 1,
        "target": 2,
        "type": "uses",
        "description": "ML uses Neural Networks"
      }
    ]
  }
}
```

---

## Database Schema

### SQL Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER,
    file_path VARCHAR(500),
    collection_name VARCHAR(255) NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'processing',
    error_message TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Entities table
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    description TEXT,
    document_id INTEGER NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Relationships table
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relationship_type VARCHAR(100) NOT NULL,
    description TEXT,
    source_entity_id INTEGER NOT NULL,
    target_entity_id INTEGER NOT NULL,
    FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_entities_document_id ON entities(document_id);
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX idx_relationships_target ON relationships(target_entity_id);
```

### Neo4j Schema

```cypher
// Entity node
CREATE (e:Entity {
    id: 1,
    name: "Machine Learning",
    type: "CONCEPT",
    description: "A method of data analysis",
    document_id: 5,
    user_id: 1
})

// Relationship edge
CREATE (e1:Entity {id: 1})-[r:RELATED {
    id: 1,
    type: "uses",
    description: "ML uses Neural Networks"
}]->(e2:Entity {id: 2})

// Indexes
CREATE INDEX entity_id FOR (e:Entity) ON (e.id);
CREATE INDEX entity_user FOR (e:Entity) ON (e.user_id);
CREATE INDEX entity_document FOR (e:Entity) ON (e.document_id);
CREATE INDEX entity_name FOR (e:Entity) ON (e.name);
```

---

## Security Implementation

### 1. Password Security

**Hashing**:
- Algorithm: bcrypt
- Cost factor: 12 (2^12 iterations)
- Salt: Automatically generated per password
- Output: 60-character hash

**Example**:
```
Password: "MySecurePass123"
Hash: "$2b$12$KIXqVfSO4k8I9x.3OqGMpO7qJ0jQZY1IvP.eiZq3NZpWZq3X8pYqS"
```

### 2. JWT Tokens

**Structure**:
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "alice",
    "exp": 1640995200
  },
  "signature": "..."
}
```

**Verification Process**:
1. Extract token from `Authorization: Bearer <token>` header
2. Decode token
3. Verify signature using SECRET_KEY
4. Check expiration time
5. Load user from database
6. Attach user to request

### 3. Data Isolation

**Per-User Collections**:
- Qdrant: `user_{id}_doc_{doc_id}`
- Neo4j: Filter by `user_id` property
- SQL: Foreign key constraints

**Query Examples**:
```sql
-- Only user's documents
SELECT * FROM documents WHERE user_id = current_user.id;

-- Only user's entities
SELECT e.* FROM entities e
JOIN documents d ON e.document_id = d.id
WHERE d.user_id = current_user.id;
```

### 4. Input Validation

**Pydantic Schemas**:
```python
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    use_graph: bool = True
```

---

## Deployment Guide

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run application
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

**1. Environment Setup**:
```bash
# Use production settings
USE_NEO4J=true
DATABASE_URL=postgresql://user:pass@localhost/graphrag
SECRET_KEY=<strong-random-key>
```

**2. Database Migration**:
```bash
# Use PostgreSQL instead of SQLite
DATABASE_URL=postgresql://user:pass@host:5432/graphrag
```

**3. Reverse Proxy (NGINX)**:
```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**4. Process Manager (Systemd)**:
```ini
[Unit]
Description=Graph RAG API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/graph-rag
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**5. Docker Deployment**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/graphrag
    depends_on:
      - db
      - neo4j

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: graphrag
      POSTGRES_PASSWORD: password

  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password
```

---

## Performance Optimization

### 1. Database Indexes

```sql
-- Critical indexes
CREATE INDEX CONCURRENTLY idx_documents_user_status
ON documents(user_id, status);

CREATE INDEX CONCURRENTLY idx_entities_document_name
ON entities(document_id, name);
```

### 2. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_vectorstore(collection_name: str):
    """Cache vectorstore instances"""
    return QdrantVectorStore(
        client=get_qdrant_client(),
        embedding=embeddings,
        collection_name=collection_name
    )
```

### 3. Batch Processing

```python
# Process documents in batches
async def process_documents_batch(documents: List[str]):
    tasks = [process_document(doc) for doc in documents]
    await asyncio.gather(*tasks)
```

### 4. Connection Pooling

```python
# SQLAlchemy connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### 5. Monitoring

```python
import time

@router.post("/query/")
async def query_endpoint(request: QueryRequest):
    start_time = time.time()

    result = await rag_service.query(...)

    duration = time.time() - start_time
    print(f"Query processed in {duration:.2f}s")

    return result
```

---

## Summary

This Graph RAG system combines:

- **FastAPI** for high-performance API
- **Qdrant** for vector search
- **Neo4j/SQL** for graph storage
- **Google Gemini** for embeddings and LLM
- **JWT** for authentication
- **LangChain** for document processing

**Key Strengths**:
- Multi-tenant architecture
- Flexible graph storage (SQL or Neo4j)
- Comprehensive entity extraction
- Graph-enhanced retrieval
- Production-ready security
- Scalable design

**Performance**:
- Document upload: ~10-30 seconds
- Query response: ~1-3 seconds
- Supports thousands of documents per user
- Scales horizontally with load balancing

**Next Steps**:
1. Install dependencies: `pip install -r requirements.txt`
2. Configure .env with API keys
3. Start application: `python main.py`
4. Test with interactive docs: http://localhost:8000/docs

For questions, refer to:
- [README.md](README.md) - Getting started
- [API_GUIDE.md](API_GUIDE.md) - API usage
- [NEO4J_SETUP.md](NEO4J_SETUP.md) - Graph database setup
