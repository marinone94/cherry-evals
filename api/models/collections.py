"""Pydantic models for collection endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    """Request model for creating a collection."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class CollectionUpdate(BaseModel):
    """Request model for updating a collection."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class CollectionResponse(BaseModel):
    """Response model for a single collection."""

    id: int
    name: str
    description: str | None
    user_id: str | None
    example_count: int
    created_at: datetime
    updated_at: datetime


class CollectionListResponse(BaseModel):
    """Response model for listing collections."""

    collections: list[CollectionResponse]
    total: int


class AddExamplesRequest(BaseModel):
    """Request model for adding examples to a collection."""

    example_ids: list[int] = Field(..., min_length=1)


class RemoveExamplesRequest(BaseModel):
    """Request model for bulk removing examples from a collection."""

    example_ids: list[int] = Field(..., min_length=1)


class CollectionExampleResponse(BaseModel):
    """Response model for an example within a collection."""

    id: int
    dataset_id: int
    question: str
    answer: str | None
    choices: list[str] | None
    example_metadata: dict[str, Any] | None
    added_at: datetime

    model_config = {"from_attributes": True}


class CollectionExamplesListResponse(BaseModel):
    """Response model for listing examples in a collection."""

    examples: list[CollectionExampleResponse]
    total: int
    collection_id: int
