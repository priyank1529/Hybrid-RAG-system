from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Qdrant Configuration
    qdrant_url: str
    qdrant_api_key: str

    # Google AI Configuration
    google_api_key: str

    # OpenAI Configuration (optional)
    openai_api_key: str = ""

    # Application Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./graph_rag.db"

    # Neo4j Graph Database (optional)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    use_neo4j: bool = False

    # Application settings
    upload_dir: str = "uploads"
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
