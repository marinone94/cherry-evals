"""Agent-powered API endpoints — LLM-driven ingestion, export, and discovery."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import check_and_increment_llm_budget, get_current_user, require_paid
from cherry_evals.config import settings
from core.traces.events import record_event
from db.postgres.base import get_db
from db.postgres.models import Collection, CollectionExample, Dataset, Example, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class DiscoverDatasetRequest(BaseModel):
    """Request to discover a dataset."""

    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="What kind of dataset to find, or a HuggingFace ID",
    )


class IngestDatasetRequest(BaseModel):
    """Request to ingest an arbitrary dataset."""

    description: str = Field(
        ..., min_length=1, max_length=500, description="Description of what to ingest"
    )
    hf_dataset_id: str | None = Field(
        None,
        max_length=200,
        pattern=r"^[\w\-./]+$",
        description="Direct HuggingFace dataset ID",
    )
    hf_config: str | None = Field(
        None, max_length=200, description="HuggingFace config/subset name"
    )
    max_examples: int | None = Field(
        None, ge=1, le=100_000, description="Limit on examples to ingest"
    )


class CustomExportRequest(BaseModel):
    """Request to export a collection in a custom format."""

    format_description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Target format description (e.g. 'Inspect AI', 'LangSmith', or custom)",
    )


class DiscoverResponse(BaseModel):
    """Response from dataset discovery."""

    hf_dataset_id: str | None = None
    name: str | None = None
    description: str | None = None
    task_type: str | None = None
    license: str | None = None
    splits: list[str] | None = None
    rationale: str | None = None
    error: str | None = None


class IngestResponse(BaseModel):
    """Response from agentic ingestion."""

    success: bool
    dataset_name: str
    total_examples: int = 0
    splits: dict[str, int] = {}
    explanation: str | None = None
    adapter_code_available: bool = False
    errors: list[str] = []


class CustomExportResponse(BaseModel):
    """Response from custom export."""

    success: bool
    num_examples: int = 0
    file_extension: str = ".txt"
    content_type: str = "text/plain"
    explanation: str | None = None
    errors: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/discover",
    response_model=DiscoverResponse,
    dependencies=[Depends(require_paid), Depends(check_and_increment_llm_budget)],
)
def discover_dataset(request: DiscoverDatasetRequest):
    """Discover a HuggingFace dataset matching a description.

    Uses an LLM to find the best matching dataset. You can also pass a
    direct HuggingFace dataset ID to get its metadata.
    """
    from agents.ingestion_agent import IngestionAgent

    agent = IngestionAgent()
    result = agent.discover_dataset(request.description)
    if not result:
        return DiscoverResponse(error="No matching dataset found.")
    return DiscoverResponse(
        hf_dataset_id=result.get("hf_dataset_id"),
        name=result.get("name"),
        description=result.get("description"),
        task_type=result.get("task_type"),
        license=result.get("license"),
        splits=result.get("splits"),
        rationale=result.get("rationale"),
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    dependencies=[Depends(require_paid), Depends(check_and_increment_llm_budget)],
)
def ingest_dataset(
    request: IngestDatasetRequest,
    x_session_id: str | None = Header(default=None),
):
    """Ingest an arbitrary HuggingFace dataset using LLM-generated parsing logic.

    The agent discovers the dataset, inspects its schema, generates a parser,
    validates it, and runs ingestion. For known datasets (mmlu, humaneval, etc.),
    use the standard CLI ingest command instead.
    """
    from agents.ingestion_agent import IngestionAgent

    agent = IngestionAgent(max_examples=request.max_examples)
    result = agent.ingest(
        description=request.description,
        hf_dataset_id=request.hf_dataset_id,
        hf_config=request.hf_config,
    )

    return IngestResponse(
        success=result.success,
        dataset_name=result.dataset_name,
        total_examples=result.total_examples,
        splits=result.splits,
        explanation=result.plan.explanation if result.plan else None,
        adapter_code_available=result.adapter_code is not None,
        errors=result.errors,
    )


@router.post(
    "/{collection_id}/export-custom",
    dependencies=[Depends(require_paid), Depends(check_and_increment_llm_budget)],
)
def export_collection_custom(
    collection_id: int,
    request: CustomExportRequest,
    db: Session = Depends(get_db),
    x_session_id: str | None = Header(default=None),
    user: User | None = Depends(get_current_user),
):
    """Export a collection to any format using LLM-generated conversion logic.

    For standard formats (json, jsonl, csv, langfuse), use the regular export
    endpoint. This endpoint handles custom formats like 'Inspect AI', 'LangSmith',
    'EleutherAI harness', or any user-described schema.
    """
    from agents.export_agent import ExportAgent

    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Ownership check — prevent IDOR
    if settings.auth_enabled and user is not None:
        if collection.user_id != user.supabase_id:
            raise HTTPException(status_code=404, detail="Collection not found")

    examples = (
        db.execute(
            select(Example)
            .join(CollectionExample, CollectionExample.example_id == Example.id)
            .where(CollectionExample.collection_id == collection_id)
            .order_by(CollectionExample.added_at)
        )
        .scalars()
        .all()
    )

    dataset_ids = {ex.dataset_id for ex in examples}
    dataset_names = {}
    if dataset_ids:
        datasets = db.execute(select(Dataset).where(Dataset.id.in_(dataset_ids))).scalars().all()
        dataset_names = {ds.id: ds.name for ds in datasets}

    agent = ExportAgent()
    result = agent.export(examples, request.format_description, dataset_names)

    # Record event
    try:
        record_event(
            db=db,
            event_type="export",
            session_id=x_session_id,
            collection_id=collection_id,
            export_format=f"custom:{request.format_description[:50]}",
        )
    except Exception:
        logger.exception("Failed to record custom export event")

    if not result.success:
        return CustomExportResponse(
            success=False,
            num_examples=result.num_examples,
            file_extension=result.file_extension,
            content_type=result.content_type,
            explanation=result.plan.explanation if result.plan else None,
            errors=result.errors,
        )

    # Return as downloadable file
    filename = f"{collection.name.replace(' ', '_').lower()}{result.file_extension}"
    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
