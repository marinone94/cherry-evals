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


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., min_length=1, description="Natural language search query")
    subject: str | None = Field(None, description="Filter by subject")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    score_threshold: float | None = Field(None, ge=0, le=1, description="Min similarity score")
    collection: str = Field("mmlu_embeddings", description="Qdrant collection to search")


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search."""

    query: str = Field(..., min_length=1, description="Search query string")
    dataset: str | None = Field(None, description="Filter by dataset name")
    subject: str | None = Field(None, description="Filter by subject")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")
    keyword_weight: float = Field(0.4, ge=0, le=1, description="Weight for keyword results")
    semantic_weight: float = Field(0.6, ge=0, le=1, description="Weight for semantic results")
    collection: str = Field("mmlu_embeddings", description="Qdrant collection to search")


class IntelligentSearchRequest(BaseModel):
    """Request model for LLM-powered intelligent search."""

    query: str = Field(..., min_length=1, description="Natural language search query")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")


class IntelligentSearchResponse(SearchResponse):
    """Response model for intelligent search, extending SearchResponse with metadata."""

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Query understanding and re-ranking metadata",
    )
