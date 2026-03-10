"""Pydantic models for search endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for keyword search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    dataset: str | None = Field(None, max_length=100, description="Filter by dataset name")
    subject: str | None = Field(None, max_length=100, description="Filter by subject")
    task_type: str | None = Field(None, max_length=100, description="Filter by dataset task_type")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")
    sort_by: str = Field(
        "relevance",
        description="Sort order: 'relevance' (by id), 'newest' (created_at desc), 'dataset'",
    )


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

    query: str = Field(
        ..., min_length=1, max_length=500, description="Natural language search query"
    )
    subject: str | None = Field(None, max_length=100, description="Filter by subject")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    score_threshold: float | None = Field(None, ge=0, le=1, description="Min similarity score")
    collection: str = Field(
        "mmlu_embeddings", max_length=100, description="Qdrant collection to search"
    )


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    dataset: str | None = Field(None, max_length=100, description="Filter by dataset name")
    subject: str | None = Field(None, max_length=100, description="Filter by subject")
    task_type: str | None = Field(None, max_length=100, description="Filter by dataset task_type")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")
    keyword_weight: float = Field(0.4, ge=0, le=1, description="Weight for keyword results")
    semantic_weight: float = Field(0.6, ge=0, le=1, description="Weight for semantic results")
    collection: str = Field(
        "mmlu_embeddings", max_length=100, description="Qdrant collection to search"
    )


class SearchIterationModel(BaseModel):
    """A single iteration performed by the autonomous search agent."""

    tool_used: str
    query: str
    filters: dict[str, Any]
    result_count: int
    evaluation: str | None = None


class IntelligentSearchRequest(BaseModel):
    """Request model for LLM-powered intelligent search."""

    query: str = Field(
        ..., min_length=1, max_length=500, description="Natural language search query"
    )
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")
    strategy: str = Field(
        "agent",
        description=(
            "Search strategy: 'agent' (autonomous iterative agent, default) "
            "or 'pipeline' (fixed parse→search→rerank DAG)"
        ),
    )
    max_iterations: int = Field(
        3,
        ge=1,
        le=5,
        description="Maximum agent iterations (only used when strategy='agent')",
    )


class IntelligentSearchResponse(SearchResponse):
    """Response model for intelligent search, extending SearchResponse with metadata."""

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Query understanding and re-ranking metadata",
    )
    iterations: list[SearchIterationModel] = Field(
        default_factory=list,
        description="Agent iteration trace (populated when strategy='agent')",
    )
    final_evaluation: str = Field(
        default="",
        description="Agent's final quality assessment (populated when strategy='agent')",
    )
    query_understanding: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial query understanding / search plan",
    )
    strategy_used: str = Field(
        default="pipeline",
        description="Which strategy was used: 'agent' or 'pipeline'",
    )


class FacetRequest(BaseModel):
    """Request model for faceted search counts."""

    query: str | None = Field(
        None, max_length=500, description="Optional keyword; if None, counts all examples"
    )


class FacetResponse(BaseModel):
    """Response model for faceted search counts."""

    datasets: list[dict[str, Any]] = Field(description='[{"name": "MMLU", "count": 14042}, ...]')
    subjects: list[dict[str, Any]] = Field(
        description='[{"name": "anatomy", "dataset": "MMLU", "count": 135}, ...]'
    )
    task_types: list[dict[str, Any]] = Field(
        description='[{"name": "multiple_choice", "count": 14042}, ...]'
    )
    total: int
