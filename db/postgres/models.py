"""SQLAlchemy database models."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres.base import Base


class Dataset(Base):
    """Dataset model."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    examples: Mapped[list["Example"]] = relationship("Example", back_populates="dataset")


class Example(Base):
    """Example model."""

    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    choices: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="examples")
    collection_examples: Mapped[list["CollectionExample"]] = relationship(
        "CollectionExample", back_populates="example"
    )

    # Indexes
    __table_args__ = (Index("ix_examples_dataset_id", "dataset_id"),)


class Collection(Base):
    """Collection model."""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    collection_examples: Mapped[list["CollectionExample"]] = relationship(
        "CollectionExample", back_populates="collection", cascade="all, delete-orphan"
    )


class CollectionExample(Base):
    """Join table for collections and examples."""

    __tablename__ = "collection_examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    collection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    example_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("examples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="collection_examples"
    )
    example: Mapped["Example"] = relationship("Example", back_populates="collection_examples")

    # Indexes and constraints
    __table_args__ = (
        Index("ix_collection_examples_collection_id", "collection_id"),
        Index("ix_collection_examples_example_id", "example_id"),
        Index(
            "ix_collection_examples_unique",
            "collection_id",
            "example_id",
            unique=True,
        ),
    )
