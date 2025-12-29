# Quick Reference Guide

## 🚀 Start the Server

```bash
./start.sh
# or
python main.py
```

Server runs at: **http://localhost:8000**

## 📖 Documentation URLs

- Interactive API Docs: http://localhost:8000/docs
- API Reference: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## 🔑 Common Commands

### 1. Register User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@email.com","password":"pass123"}'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -d "username=user&password=pass123"
```

### 3. Upload Document

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf"
```

### 4. List Documents

```bash
curl -X GET "http://localhost:8000/api/documents/" \
  -H "Authorization: Bearer TOKEN"
```

### 5. Query Documents

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is this about?","top_k":5,"use_graph":true}'
```

### 6. Get Knowledge Graph

```bash
curl -X GET "http://localhost:8000/api/graph/user" \
  -H "Authorization: Bearer TOKEN"
```

## 🐍 Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
r = requests.post(f"{BASE_URL}/api/auth/login",
                  data={"username":"user","password":"pass123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload
with open("doc.pdf", "rb") as f:
    r = requests.post(f"{BASE_URL}/api/documents/upload",
                      headers=headers, files={"file": f})

# Query
r = requests.post(f"{BASE_URL}/api/query/",
                  headers=headers,
                  json={"query": "What is this about?", "top_k": 5})
print(r.json()["answer"])
```

## 📂 File Structure

```
graph-rag/
├── main.py              # Run this
├── .env                 # Configure this
├── src/                 # Source code
├── uploads/             # User files
└── graph_rag.db         # Database
```

## ⚙️ Environment Variables

```env
QDRANT_URL=https://...
QDRANT_API_KEY=...
GOOGLE_API_KEY=...
SECRET_KEY=...
```

## 🔧 Troubleshooting

### Can't connect to server
```bash
# Check if running
curl http://localhost:8000/health
```

### Database errors
```bash
# Reset database
rm graph_rag.db
python main.py
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 📊 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Get user info |
| POST | `/api/documents/upload` | Upload document |
| GET | `/api/documents/` | List documents |
| GET | `/api/documents/{id}` | Get document |
| DELETE | `/api/documents/{id}` | Delete document |
| POST | `/api/query/` | Query RAG |
| GET | `/api/graph/document/{id}` | Get doc graph |
| GET | `/api/graph/user` | Get user graph |

## 🎯 Supported File Types

- ✅ PDF (`.pdf`)
- ✅ CSV (`.csv`)
- ✅ JSON (`.json`)
- ✅ Text (`.txt`)
- ✅ Web URLs (`https://...`)

## 🧪 Run Tests

```bash
python test_api.py
```

## 📚 Documentation Files

- `README.md` - Full documentation
- `SETUP.md` - Setup guide
- `API_GUIDE.md` - API reference
- `ARCHITECTURE.md` - Architecture details
- `PROJECT_SUMMARY.md` - What was built
- `QUICK_REFERENCE.md` - This file

## 💡 Tips

1. Always include `Authorization: Bearer TOKEN` header
2. Token expires in 30 minutes
3. Each user has isolated documents
4. Documents are stored in `uploads/user_{id}/`
5. Use interactive docs for easy testing: `/docs`

## 🔒 Security Reminders

- Change `SECRET_KEY` in `.env` for production
- Don't commit `.env` to git
- Keep API keys secure
- Use HTTPS in production

## 🎨 Next Steps

1. ✅ Start the server
2. ✅ Register a user
3. ✅ Upload documents
4. ✅ Query your data
5. 🚀 Build a frontend!

---

**Need Help?**
- Read: `README.md`
- Test: `python test_api.py`
- Docs: http://localhost:8000/docs
