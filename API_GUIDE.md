# Graph RAG API Usage Guide

Complete guide for using the Graph RAG API endpoints.

## Quick Start

1. **Start the server**
   ```bash
   ./start.sh
   # or
   python main.py
   ```

2. **Access interactive docs**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Authentication Flow

### 1. Register a New User

**Endpoint:** `POST /api/auth/register`

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00"
}
```

### 2. Login

**Endpoint:** `POST /api/auth/login`

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=SecurePass123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the token** for subsequent requests!

### 3. Get Current User Info

**Endpoint:** `GET /api/auth/me`

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Document Management

### Upload a Document

**Endpoint:** `POST /api/documents/upload`

**Supported file types:** PDF, CSV, JSON, TXT

```bash
# Upload PDF
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"

# Upload CSV
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/data.csv"

# Upload Text File
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/notes.txt"
```

**Response:**
```json
{
  "id": 1,
  "filename": "document.pdf",
  "original_filename": "document.pdf",
  "file_type": "pdf",
  "file_size": 524288,
  "collection_name": "user_1_doc_1",
  "chunk_count": 42,
  "status": "completed",
  "error_message": null,
  "uploaded_at": "2024-01-01T12:00:00",
  "processed_at": "2024-01-01T12:00:15",
  "user_id": 1
}
```

### List All Documents (Dashboard)

**Endpoint:** `GET /api/documents/`

```bash
curl -X GET "http://localhost:8000/api/documents/?skip=0&limit=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total": 3,
  "documents": [
    {
      "id": 1,
      "filename": "research_paper.pdf",
      "file_type": "pdf",
      "chunk_count": 42,
      "status": "completed",
      "uploaded_at": "2024-01-01T12:00:00"
    },
    {
      "id": 2,
      "filename": "data.csv",
      "file_type": "csv",
      "chunk_count": 15,
      "status": "completed",
      "uploaded_at": "2024-01-02T10:30:00"
    },
    {
      "id": 3,
      "filename": "notes.txt",
      "file_type": "txt",
      "chunk_count": 8,
      "status": "processing",
      "uploaded_at": "2024-01-03T09:15:00"
    }
  ]
}
```

### Get Specific Document

**Endpoint:** `GET /api/documents/{document_id}`

```bash
curl -X GET "http://localhost:8000/api/documents/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Delete a Document

**Endpoint:** `DELETE /api/documents/{document_id}`

```bash
curl -X DELETE "http://localhost:8000/api/documents/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:** `204 No Content`

This will delete:
- The physical file
- Vector embeddings from Qdrant
- Metadata from database
- Associated entities and relationships

## Querying Documents (RAG)

### Basic Query

**Endpoint:** `POST /api/query/`

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main findings in the research?",
    "top_k": 5,
    "use_graph": true
  }'
```

**Request Parameters:**
- `query` (required): Your question
- `top_k` (optional, default=5): Number of chunks to retrieve
- `use_graph` (optional, default=true): Use graph-enhanced retrieval
- `document_ids` (optional): Filter by specific documents

**Response:**
```json
{
  "query": "What are the main findings in the research?",
  "answer": "Based on the research papers, the main findings include:\n1. Graph-based RAG improves retrieval accuracy by 23%\n2. Entity relationships provide better context for LLMs\n3. Multi-hop reasoning enables more comprehensive answers",
  "retrieved_chunks": [
    {
      "content": "Our experiments show that graph-based RAG...",
      "score": 0.89,
      "document_id": 1,
      "metadata": {"filename": "research_paper.pdf"}
    }
  ],
  "entities_found": [
    {
      "id": 1,
      "name": "Graph RAG",
      "entity_type": "TECHNOLOGY",
      "description": "A retrieval method using knowledge graphs",
      "document_id": 1
    }
  ],
  "graph_context": {
    "nodes": [...],
    "edges": [...]
  }
}
```

### Query Specific Documents

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize the key points",
    "top_k": 3,
    "use_graph": true,
    "document_ids": [1, 2]
  }'
```

### Query Without Graph Enhancement

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is mentioned about AI?",
    "use_graph": false
  }'
```

## Knowledge Graph Visualization

### Get Document Graph

**Endpoint:** `GET /api/graph/document/{document_id}`

```bash
curl -X GET "http://localhost:8000/api/graph/document/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "nodes": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "type": "PERSON",
      "description": "Lead researcher"
    },
    {
      "id": 2,
      "name": "Stanford University",
      "type": "ORGANIZATION",
      "description": "Research institution"
    }
  ],
  "edges": [
    {
      "source": 1,
      "target": 2,
      "type": "works_at",
      "description": "Employment relationship"
    }
  ]
}
```

### Get Combined User Graph

**Endpoint:** `GET /api/graph/user`

```bash
# All documents
curl -X GET "http://localhost:8000/api/graph/user" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Specific documents
curl -X GET "http://localhost:8000/api/graph/user?document_ids=1&document_ids=2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Python Client Example

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "alice"
PASSWORD = "SecurePass123"

# 1. Login
response = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={"username": USERNAME, "password": PASSWORD}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Upload a document
with open("document.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        files={"file": f}
    )
    document = response.json()
    print(f"Uploaded: {document['filename']}")

# 3. List documents
response = requests.get(f"{BASE_URL}/api/documents/", headers=headers)
documents = response.json()
print(f"Total documents: {documents['total']}")

# 4. Query documents
response = requests.post(
    f"{BASE_URL}/api/query/",
    headers=headers,
    json={
        "query": "What is this document about?",
        "top_k": 5,
        "use_graph": True
    }
)
result = response.json()
print(f"Answer: {result['answer']}")

# 5. Get knowledge graph
response = requests.get(f"{BASE_URL}/api/graph/user", headers=headers)
graph = response.json()
print(f"Entities: {len(graph['nodes'])}, Relationships: {len(graph['edges'])}")
```

## Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

Currently no rate limiting is implemented. Consider adding it for production use.

## Best Practices

1. **Token Management**
   - Store tokens securely
   - Refresh tokens before expiry
   - Don't commit tokens to version control

2. **Document Upload**
   - Upload documents in batches if possible
   - Check status before querying new documents
   - Delete unused documents to save storage

3. **Querying**
   - Use specific queries for better results
   - Adjust `top_k` based on your needs
   - Enable graph enhancement for complex queries
   - Filter by `document_ids` for targeted searches

4. **Graph Visualization**
   - Use for understanding document relationships
   - Helps identify key entities across documents
   - Useful for exploratory analysis

## Troubleshooting

### "Could not validate credentials"
- Check if token is valid and not expired
- Verify token is included in `Authorization` header

### "Document not found"
- Ensure document belongs to authenticated user
- Check document ID is correct

### "Error processing document"
- Check file format is supported
- Verify file is not corrupted
- Check API key configuration in `.env`

### Slow query responses
- Reduce `top_k` value
- Disable graph enhancement for simple queries
- Consider upgrading Qdrant instance
