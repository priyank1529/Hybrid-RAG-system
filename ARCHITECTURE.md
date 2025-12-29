# Graph RAG System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  (Web Browser, Mobile App, CLI, Python Client, cURL)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│                         (main.py)                                │
├─────────────────────────────────────────────────────────────────┤
│  Routers:                                                        │
│  • /api/auth      - Authentication & User Management            │
│  • /api/documents - Document Upload & Management                │
│  • /api/query     - RAG Query Interface                         │
│  • /api/graph     - Knowledge Graph Visualization               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Services:                                                       │
│  • DocumentProcessor  - File loading, chunking, processing      │
│  • GraphRAGService    - Entity extraction, relationships        │
│  • RAGService         - Query processing, answer generation     │
└─────────────────────────────────────────────────────────────────┘
                    ↓                        ↓
┌──────────────────────────┐    ┌───────────────────────────────┐
│   Storage Layer          │    │    External Services          │
├──────────────────────────┤    ├───────────────────────────────┤
│ • SQLite/PostgreSQL      │    │ • Google Gemini (Embeddings)  │
│   - User data            │    │ • Google Gemini (LLM)         │
│   - Document metadata    │    │ • Qdrant (Vector DB)          │
│   - Entities             │    │                               │
│   - Relationships        │    │                               │
│                          │    │                               │
│ • File System            │    │                               │
│   - Uploaded documents   │    │                               │
└──────────────────────────┘    └───────────────────────────────┘
```

## Detailed Component Architecture

### 1. API Layer (`src/api/`)

```
┌─────────────────────────────────────────────────────────┐
│                    API Endpoints                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  auth.py                                                 │
│  ├── POST /api/auth/register                            │
│  ├── POST /api/auth/login                               │
│  └── GET  /api/auth/me                                  │
│                                                          │
│  documents.py                                            │
│  ├── POST   /api/documents/upload                       │
│  ├── GET    /api/documents/                             │
│  ├── GET    /api/documents/{id}                         │
│  └── DELETE /api/documents/{id}                         │
│                                                          │
│  query.py                                                │
│  └── POST /api/query/                                   │
│                                                          │
│  graph.py                                                │
│  ├── GET /api/graph/document/{id}                       │
│  └── GET /api/graph/user                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2. Document Processing Pipeline

```
User Upload
    ↓
┌─────────────────────────────────────────────┐
│ 1. File Reception & Storage                 │
│    - Save to file system                    │
│    - Create DB record                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 2. Document Loading                         │
│    - Detect file type                       │
│    - Load content (PDF/CSV/JSON/TXT/URL)    │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 3. Text Chunking                            │
│    - RecursiveCharacterTextSplitter         │
│    - chunk_size: 500                        │
│    - chunk_overlap: 50                      │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 4. Embedding Generation                     │
│    - Google Gemini Embeddings               │
│    - model: gemini-embedding-001            │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 5. Vector Storage                           │
│    - Store in Qdrant                        │
│    - Collection: user_{id}_doc_{doc_id}     │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 6. Entity Extraction (Graph RAG)            │
│    - LLM-based entity extraction            │
│    - Relationship identification            │
│    - Store in database                      │
└─────────────────────────────────────────────┘
    ↓
Processing Complete
```

### 3. RAG Query Pipeline

```
User Query
    ↓
┌─────────────────────────────────────────────┐
│ 1. Query Embedding                          │
│    - Embed query with same model            │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 2. Vector Similarity Search                 │
│    - Search Qdrant collections              │
│    - Retrieve top_k similar chunks          │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 3. Graph Enhancement (if enabled)           │
│    - Find relevant entities                 │
│    - Traverse relationships                 │
│    - Enrich context                         │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 4. Context Building                         │
│    - Combine retrieved chunks               │
│    - Add entity information                 │
│    - Include relationships                  │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 5. Answer Generation                        │
│    - LLM: Google Gemini Pro                 │
│    - Context-aware generation               │
└─────────────────────────────────────────────┘
    ↓
Response to User
```

### 4. Database Schema

```sql
┌─────────────────────┐
│      Users          │
├─────────────────────┤
│ • id (PK)           │
│ • username          │
│ • email             │
│ • hashed_password   │
│ • is_active         │
│ • created_at        │
└─────────────────────┘
         ↓ 1:N
┌─────────────────────┐
│    Documents        │
├─────────────────────┤
│ • id (PK)           │
│ • user_id (FK)      │
│ • filename          │
│ • file_type         │
│ • file_path         │
│ • collection_name   │
│ • chunk_count       │
│ • status            │
│ • uploaded_at       │
│ • processed_at      │
└─────────────────────┘
         ↓ 1:N
┌─────────────────────┐
│     Entities        │
├─────────────────────┤
│ • id (PK)           │
│ • document_id (FK)  │
│ • name              │
│ • entity_type       │
│ • description       │
└─────────────────────┘
    ↓            ↓
    ├────────────┤
    │            │
┌──────────────────────┐
│   Relationships      │
├──────────────────────┤
│ • id (PK)            │
│ • source_entity (FK) │
│ • target_entity (FK) │
│ • relationship_type  │
│ • description        │
└──────────────────────┘
```

### 5. Authentication Flow

```
┌────────────┐
│   Client   │
└────────────┘
      ↓
   Register
      ↓
┌────────────────────────────────┐
│ 1. Validate Input              │
│ 2. Check Username/Email Unique │
│ 3. Hash Password (bcrypt)      │
│ 4. Create User Record          │
└────────────────────────────────┘
      ↓
   Login
      ↓
┌────────────────────────────────┐
│ 1. Verify Credentials          │
│ 2. Generate JWT Token          │
│    - Expires in 30 min         │
│    - Signed with SECRET_KEY    │
└────────────────────────────────┘
      ↓
   Protected Endpoints
      ↓
┌────────────────────────────────┐
│ 1. Extract Token from Header   │
│ 2. Verify JWT Signature        │
│ 3. Check Expiration            │
│ 4. Load User from DB           │
│ 5. Attach to Request           │
└────────────────────────────────┘
```

### 6. Graph RAG Enhancement

```
┌─────────────────────────────────────────────┐
│         Traditional RAG                      │
│                                              │
│  Query → Vector Search → Retrieved Chunks   │
│                                              │
│  Limitation: No relationships context       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         Graph-Enhanced RAG                   │
│                                              │
│  Query → Vector Search → Retrieved Chunks   │
│            ↓                                 │
│       Entity Detection                       │
│            ↓                                 │
│    Relationship Traversal                    │
│            ↓                                 │
│     Enriched Context                         │
│                                              │
│  Benefit: Multi-hop reasoning, better        │
│           context understanding              │
└─────────────────────────────────────────────┘
```

### 7. Data Flow Example

**User uploads "research_paper.pdf":**

```
1. Upload File
   └─> uploads/user_1/research_paper.pdf

2. Create DB Record
   └─> documents table: id=1, user_id=1, status='processing'

3. Extract & Chunk
   └─> 42 chunks created

4. Generate Embeddings
   └─> 42 vectors (768 dimensions each)

5. Store in Qdrant
   └─> Collection: user_1_doc_1
   └─> 42 vectors stored

6. Extract Entities
   └─> Found:
       - "Dr. Alice Johnson" (PERSON)
       - "Stanford University" (ORGANIZATION)
       - "Machine Learning" (TECHNOLOGY)
       - "Neural Networks" (CONCEPT)

7. Extract Relationships
   └─> Created:
       - Dr. Alice Johnson → works_at → Stanford University
       - Dr. Alice Johnson → researches → Machine Learning
       - Machine Learning → uses → Neural Networks

8. Update Status
   └─> documents table: status='completed', chunk_count=42
```

**User queries "Who researches machine learning?":**

```
1. Embed Query
   └─> Vector: [0.123, -0.456, ...]

2. Search Qdrant
   └─> Top 5 chunks retrieved
   └─> Scores: [0.89, 0.85, 0.82, 0.78, 0.75]

3. Find Entities
   └─> Match: "Machine Learning"

4. Traverse Graph
   └─> Relationships:
       - Dr. Alice Johnson → researches → Machine Learning
       - Machine Learning → uses → Neural Networks

5. Build Context
   └─> Chunks: [chunk1, chunk2, chunk3, chunk4, chunk5]
   └─> Entities: [Dr. Alice Johnson, Machine Learning, ...]
   └─> Relationships: [researches, uses, ...]

6. Generate Answer
   └─> LLM processes enriched context
   └─> Answer: "Dr. Alice Johnson from Stanford University
       researches Machine Learning, specifically focusing
       on Neural Networks."
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.119+
- **Language**: Python 3.12+
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)

### Database
- **Relational**: SQLAlchemy (SQLite/PostgreSQL)
- **Vector**: Qdrant Cloud
- **ORM**: SQLAlchemy 2.0+

### AI/ML
- **Embeddings**: Google Gemini (gemini-embedding-001)
- **LLM**: Google Gemini Pro
- **Framework**: LangChain 1.0+

### Document Processing
- **PDF**: PyMuPDF
- **Text**: LangChain TextLoader
- **CSV**: LangChain CSVLoader
- **JSON**: LangChain JSONLoader
- **Web**: LangChain WebBaseLoader

## Scalability Considerations

### Current Design (Single Server)
- SQLite database
- File system storage
- Single process

### Production Recommendations
1. **Database**: PostgreSQL with connection pooling
2. **Storage**: S3 or cloud storage
3. **Caching**: Redis for session management
4. **Queue**: Celery for async document processing
5. **Load Balancer**: NGINX or cloud LB
6. **Monitoring**: Prometheus + Grafana
7. **Logging**: ELK stack or cloud logging

## Security Features

1. **Authentication**
   - JWT tokens with expiration
   - bcrypt password hashing
   - Secure secret key

2. **Authorization**
   - User-specific document isolation
   - Protected endpoints with auth dependency

3. **Data Privacy**
   - Per-user Qdrant collections
   - User-scoped queries

4. **Input Validation**
   - Pydantic schemas
   - File type verification
   - Size limits

## Future Enhancements

1. **Horizontal Scaling**
   - Stateless API design (✅ Already implemented)
   - Load balancing support
   - Distributed task queue

2. **Advanced Features**
   - Collaborative document sharing
   - Real-time updates (WebSocket)
   - Advanced graph analytics
   - Custom entity types
   - Multi-modal support (images, audio)

3. **Performance**
   - Response caching
   - Batch processing
   - Async document processing
   - Query optimization

4. **Monitoring**
   - Health checks (✅ Already implemented)
   - Metrics collection
   - Error tracking
   - Usage analytics
