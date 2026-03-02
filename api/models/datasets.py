"""Pydantic models for dataset endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DatasetResponse(BaseModel):
    """Response model for a single dataset."""

    id: int
    name: str
    source: str
    license: str | None
    task_type: str
    description: str | None
    stats: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    """Response model for listing datasets."""

    datasets: list[DatasetResponse]
    total: int
