"""Export API endpoints."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.models.export import ExportFormat, ExportRequest, LangfuseExportResponse
from cherry_evals.config import settings
from core.export.formats import to_csv, to_json, to_jsonl
from core.export.langfuse_export import LangfuseExportError, export_to_langfuse
from core.traces.events import record_event
from db.postgres.base import get_db
from db.postgres.models import Collection, CollectionExample, Dataset, Example, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["export"])

_FORMAT_MEDIA_TYPES = {
    ExportFormat.json: "application/json",
    ExportFormat.jsonl: "application/x-ndjson",
    ExportFormat.csv: "text/csv",
}

_FORMAT_EXTENSIONS = {
    ExportFormat.json: "json",
    ExportFormat.jsonl: "jsonl",
    ExportFormat.csv: "csv",
}


def _get_collection_examples(db: Session, collection_id: int):
    """Fetch all examples in a collection with their dataset names."""
    rows = (
        db.execute(
            select(Example)
            .join(CollectionExample, CollectionExample.example_id == Example.id)
            .where(CollectionExample.collection_id == collection_id)
            .order_by(CollectionExample.added_at)
        )
        .scalars()
        .all()
    )

    # Build dataset_id -> name mapping
    dataset_ids = {ex.dataset_id for ex in rows}
    dataset_names = {}
    if dataset_ids:
        datasets = db.execute(select(Dataset).where(Dataset.id.in_(dataset_ids))).scalars().all()
        dataset_names = {ds.id: ds.name for ds in datasets}

    return rows, dataset_names


@router.post("/{collection_id}/export")
def export_collection(
    collection_id: int,
    request: ExportRequest,
    db: Session = Depends(get_db),
    x_session_id: str | None = Header(default=None),
    user: User | None = Depends(get_current_user),
):
    """Export a collection to the specified format.

    For json/jsonl/csv: returns the file as a download.
    For langfuse: pushes to Langfuse and returns a summary.
    """
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Ownership check — prevent IDOR
    if settings.auth_enabled and user is not None:
        if collection.user_id != user.supabase_id:
            raise HTTPException(status_code=404, detail="Collection not found")

    examples, dataset_names = _get_collection_examples(db, collection_id)

    if request.format == ExportFormat.langfuse:
        ds_name = request.langfuse_dataset_name or collection.name
        try:
            result = export_to_langfuse(
                examples,
                dataset_name=ds_name,
                dataset_description=collection.description,
                dataset_names=dataset_names,
            )
        except LangfuseExportError as e:
            raise HTTPException(status_code=502, detail=str(e))

        try:
            record_event(
                db=db,
                event_type="export",
                session_id=x_session_id,
                collection_id=collection_id,
                export_format=request.format.value,
            )
        except Exception:
            logger.exception("Failed to record langfuse export event")

        return LangfuseExportResponse(**result)

    # File-based export
    converters = {
        ExportFormat.json: to_json,
        ExportFormat.jsonl: to_jsonl,
        ExportFormat.csv: to_csv,
    }
    content = converters[request.format](examples, dataset_names)
    media_type = _FORMAT_MEDIA_TYPES[request.format]
    ext = _FORMAT_EXTENSIONS[request.format]
    filename = f"{collection.name.replace(' ', '_').lower()}.{ext}"

    try:
        record_event(
            db=db,
            event_type="export",
            session_id=x_session_id,
            collection_id=collection_id,
            export_format=request.format.value,
        )
    except Exception:
        logger.exception("Failed to record export event")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
