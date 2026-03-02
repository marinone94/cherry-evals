"""Pydantic models for example endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ExampleResponse(BaseModel):
    """Response model for a single example."""

    id: int
    dataset_id: int
    question: str
    answer: str | None
    choices: list[str] | None
    example_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExampleListResponse(BaseModel):
    """Response model for listing examples."""

    examples: list[ExampleResponse]
    total: int
    offset: int
    limit: int
