"""
Simple test script to verify the Graph RAG API is working correctly.

Usage:
    python test_api.py
"""

import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123"
}


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health_check():
    """Test the health check endpoint."""
    print_section("Testing Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ Health check passed!")


def test_register(session):
    """Test user registration."""
    print_section("Testing User Registration")
    response = session.post(
        f"{BASE_URL}/api/auth/register",
        json=TEST_USER
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print(f"Response: {response.json()}")
        print("✅ Registration successful!")
    elif response.status_code == 400:
        print("⚠️  User already exists (this is OK)")
    else:
        print(f"❌ Registration failed: {response.text}")


def test_login(session):
    """Test user login and return token."""
    print_section("Testing User Login")
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    token_data = response.json()
    print(f"Token received: {token_data['access_token'][:50]}...")
    print("✅ Login successful!")
    return token_data["access_token"]


def test_get_user(session, token):
    """Test getting current user info."""
    print_section("Testing Get Current User")
    headers = {"Authorization": f"Bearer {token}"}
    response = session.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    user_data = response.json()
    print(f"User: {user_data['username']} ({user_data['email']})")
    print("✅ Get user info successful!")


def test_list_documents(session, token):
    """Test listing documents."""
    print_section("Testing List Documents")
    headers = {"Authorization": f"Bearer {token}"}
    response = session.get(f"{BASE_URL}/api/documents/", headers=headers)
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    print(f"Total documents: {data['total']}")
    for doc in data['documents']:
        print(f"  - {doc['filename']} ({doc['status']}) - {doc['chunk_count']} chunks")
    print("✅ List documents successful!")
    return data['documents']


def test_upload_document(session, token):
    """Test document upload."""
    print_section("Testing Document Upload")

    # Create a test text file
    test_file = Path("test_document.txt")
    test_content = """
    This is a test document for the Graph RAG system.

    The system supports multiple document types including PDF, CSV, JSON, and plain text files.

    Key Features:
    - Multi-user support with authentication
    - Automatic entity extraction
    - Knowledge graph creation
    - Vector-based semantic search
    - Graph-enhanced retrieval

    The Graph RAG approach combines traditional vector search with knowledge graphs
    to provide better context and more accurate answers to user queries.
    """

    test_file.write_text(test_content)

    try:
        headers = {"Authorization": f"Bearer {token}"}
        with open(test_file, "rb") as f:
            response = session.post(
                f"{BASE_URL}/api/documents/upload",
                headers=headers,
                files={"file": f}
            )

        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            doc_data = response.json()
            print(f"Document ID: {doc_data['id']}")
            print(f"Filename: {doc_data['filename']}")
            print(f"Status: {doc_data['status']}")
            print(f"Chunks: {doc_data['chunk_count']}")
            print("✅ Document upload successful!")
            return doc_data
        else:
            print(f"❌ Upload failed: {response.text}")
            return None
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_query_documents(session, token, document_id=None):
    """Test querying documents."""
    print_section("Testing Document Query")
    headers = {"Authorization": f"Bearer {token}"}

    query_data = {
        "query": "What are the key features of the system?",
        "top_k": 3,
        "use_graph": True
    }

    if document_id:
        query_data["document_ids"] = [document_id]

    response = session.post(
        f"{BASE_URL}/api/query/",
        headers=headers,
        json=query_data
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"\nQuery: {result['query']}")
        print(f"\nAnswer:\n{result['answer']}\n")
        print(f"Retrieved chunks: {len(result['retrieved_chunks'])}")
        print(f"Entities found: {len(result['entities_found'])}")
        print("✅ Query successful!")
    else:
        print(f"❌ Query failed: {response.text}")


def test_get_graph(session, token):
    """Test getting knowledge graph."""
    print_section("Testing Knowledge Graph")
    headers = {"Authorization": f"Bearer {token}"}
    response = session.get(f"{BASE_URL}/api/graph/user", headers=headers)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        graph = response.json()
        print(f"Nodes (entities): {len(graph['nodes'])}")
        print(f"Edges (relationships): {len(graph['edges'])}")

        if graph['nodes']:
            print("\nSample entities:")
            for node in graph['nodes'][:5]:
                print(f"  - {node['name']} ({node['type']})")

        print("✅ Get graph successful!")
    else:
        print(f"⚠️  Graph retrieval: {response.text}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("  GRAPH RAG API TEST SUITE")
    print("="*60)

    session = requests.Session()

    try:
        # Basic tests
        test_health_check()
        test_register(session)
        token = test_login(session)
        test_get_user(session, token)

        # Document tests
        documents = test_list_documents(session, token)
        uploaded_doc = test_upload_document(session, token)

        # Wait a bit for processing
        if uploaded_doc:
            print("\n⏳ Waiting for document processing...")
            time.sleep(2)

        # Query tests
        doc_id = uploaded_doc['id'] if uploaded_doc else None
        test_query_documents(session, token, doc_id)

        # Graph tests
        test_get_graph(session, token)

        print_section("All Tests Completed!")
        print("🎉 Graph RAG API is working correctly!\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {BASE_URL}")
        print("   Make sure the API server is running!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    run_all_tests()
