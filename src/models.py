from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, csv, json, txt, url
    file_size = Column(Integer)  # in bytes
    file_path = Column(String)  # local storage path
    collection_name = Column(String, nullable=False)  # Qdrant collection name
    chunk_count = Column(Integer, default=0)  # number of chunks created
    status = Column(String, default="processing")  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="documents")

    entities = relationship("Entity", back_populates="document", cascade="all, delete-orphan")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)  # PERSON, ORG, LOCATION, etc.
    description = Column(Text, nullable=True)

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document = relationship("Document", back_populates="entities")

    relationships_from = relationship(
        "Relationship",
        foreign_keys="Relationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan"
    )
    relationships_to = relationship(
        "Relationship",
        foreign_keys="Relationship.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan"
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    relationship_type = Column(String, nullable=False)  # works_at, located_in, etc.
    description = Column(Text, nullable=True)

    source_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    target_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)

    source_entity = relationship("Entity", foreign_keys=[source_entity_id], back_populates="relationships_from")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id], back_populates="relationships_to")
