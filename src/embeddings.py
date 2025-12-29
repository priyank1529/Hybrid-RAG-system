from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from src.config import get_settings

settings = get_settings()


def get_embeddings(provider: str = "google"):
    """Get embeddings based on provider."""
    if provider == "google":
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.google_api_key
        )
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


# Default embeddings
embeddings = get_embeddings("google")
