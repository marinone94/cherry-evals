"""Pydantic models for search endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for keyword search."""

    query: str = Field(..., min_length=1, description="Search query string")
    dataset: str | None = Field(None, description="Filter by dataset name")
    subject: str | None = Field(None, description="Filter by subject")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")


class SearchResultItem(BaseModel):
    """A single search result."""

    id: int
    dataset_id: int
    dataset_name: str
    question: str
    answer: str | None
    choices: list[str] | None
    example_metadata: dict[str, Any] | None
    score: float | None = None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    """Response model for search results."""

    results: list[SearchResultItem]
    total: int
    query: str
    offset: int
    limit: int
