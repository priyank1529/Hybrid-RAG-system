# Quick Setup Guide

## Prerequisites

- Python 3.12+
- Qdrant instance (already configured in your .env)
- Google AI API key (already configured in your .env)

## Setup Steps

### 1. Install Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using uv (faster):
```bash
pip install uv
uv sync
```

### 2. Verify Configuration

Your `.env` file should contain:
```env
QDRANT_URL=https://bae7dec1-3924-4cd3-b4e3-02a936ca312d.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGc...
GOOGLE_API_KEY=AIzaSyB...
SECRET_KEY=your_secret_key_change_this_in_production_12345678
```

⚠️ **Important**: Change the `SECRET_KEY` to a secure random value for production!

### 3. Run the Application

Option A - Using the startup script (recommended):
```bash
chmod +x start.sh
./start.sh
```

Option B - Direct Python:
```bash
python main.py
```

The API will start on: **http://localhost:8000**

### 4. Verify Installation

Run the test suite:
```bash
python test_api.py
```

Or visit the interactive documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## First Steps

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourname",
    "email": "your@email.com",
    "password": "YourPassword123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=yourname&password=YourPassword123"
```

Save the `access_token` from the response!

### 3. Upload a Document

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/document.pdf"
```

### 4. Query Your Documents

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "top_k": 5,
    "use_graph": true
  }'
```

## Project Structure

```
graph-rag/
├── main.py                      # FastAPI application
├── .env                         # Configuration (DO NOT COMMIT!)
├── requirements.txt             # Python dependencies
├── start.sh                     # Startup script
├── test_api.py                  # API test suite
├── README.md                    # Full documentation
├── API_GUIDE.md                 # API usage guide
├── SETUP.md                     # This file
│
├── src/
│   ├── config.py                # Configuration management
│   ├── database.py              # Database setup
│   ├── models.py                # Database models
│   ├── schemas.py               # API schemas
│   ├── auth.py                  # Authentication
│   ├── embeddings.py            # Embedding models
│   │
│   ├── api/                     # API endpoints
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── documents.py         # Document management
│   │   ├── query.py             # RAG queries
│   │   └── graph.py             # Knowledge graph
│   │
│   ├── services/                # Business logic
│   │   ├── document_processor.py # Document processing
│   │   ├── graph_rag.py         # Graph RAG service
│   │   └── rag_service.py       # Query service
│   │
│   └── vectorstore/             # Vector database
│       └── qdrant.py            # Qdrant integration
│
├── uploads/                     # User uploaded files
├── data/
│   ├── raw/                     # Raw data files
│   └── processed/               # Processed data
│
└── graph_rag.db                 # SQLite database
```

## Key Features

✅ **Multi-User Support**
- User authentication with JWT tokens
- Per-user document isolation
- Secure password hashing

✅ **Document Processing**
- Support for PDF, CSV, JSON, TXT, URLs
- Automatic text extraction and chunking
- Vector embeddings with Qdrant

✅ **Graph RAG**
- Entity extraction from documents
- Relationship mapping
- Knowledge graph visualization

✅ **Advanced RAG**
- Vector-based semantic search
- Graph-enhanced retrieval
- Context-aware answers with LLM

✅ **Dashboard API**
- List all user documents
- Track processing status
- Manage document lifecycle

## Troubleshooting

### Database Issues

If you get database errors, delete the database and restart:
```bash
rm graph_rag.db
python main.py
```

### Qdrant Connection Issues

Verify your Qdrant instance is running and accessible:
```bash
curl https://bae7dec1-3924-4cd3-b4e3-02a936ca312d.us-east4-0.gcp.cloud.qdrant.io:6333/collections
```

### Import Errors

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### API Key Issues

Verify your `.env` file has valid API keys:
- GOOGLE_API_KEY: Get from https://ai.google.dev/
- QDRANT_API_KEY: Get from your Qdrant Cloud dashboard

## Security Notes

🔒 **For Production:**

1. Change `SECRET_KEY` in `.env` to a strong random value
2. Update CORS settings in `main.py`
3. Use HTTPS
4. Add rate limiting
5. Use PostgreSQL instead of SQLite
6. Enable API key rotation
7. Add request validation and sanitization

## Next Steps

1. ✅ Set up the application
2. ✅ Test with sample documents
3. 📖 Read the [API Guide](API_GUIDE.md) for detailed usage
4. 🚀 Build your application on top of this API
5. 🎨 Create a frontend dashboard
6. 📊 Visualize the knowledge graph

## Support

- Documentation: See README.md and API_GUIDE.md
- Test Suite: Run `python test_api.py`
- Interactive Docs: http://localhost:8000/docs

Happy building! 🎉
