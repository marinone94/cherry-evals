"""Pydantic models for export endpoints."""

from enum import Enum

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats."""

    json = "json"
    jsonl = "jsonl"
    csv = "csv"
    langfuse = "langfuse"


class ExportRequest(BaseModel):
    """Request model for exporting a collection."""

    format: ExportFormat
    langfuse_dataset_name: str | None = Field(
        None,
        description="Custom name for the Langfuse dataset. Defaults to collection name.",
    )


class LangfuseExportResponse(BaseModel):
    """Response for Langfuse exports."""

    dataset_name: str
    items_exported: int
