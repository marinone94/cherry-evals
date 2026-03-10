"""API key management endpoints."""

import hashlib
import logging
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import _get_limits, get_current_user
from db.postgres.base import get_db
from db.postgres.models import ApiKey, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

API_KEY_PREFIX = "ck_live_"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class CreateApiKeyRequest(BaseModel):
    """Request to create a new API key."""

    name: str = Field(default="Default", max_length=255)


class ApiKeyResponse(BaseModel):
    """API key metadata (never includes the full key)."""

    id: int
    key_prefix: str
    name: str
    last_used_at: datetime | None
    is_active: bool
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Response when creating a key — includes the plaintext key exactly once."""

    key: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
def create_api_key(
    request: CreateApiKeyRequest,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new API key. The plaintext key is returned only once."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check tier limit
    max_keys = _get_limits(user)["max_api_keys"]
    active_count = db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id, ApiKey.is_active == True)  # noqa: E712
    ).scalars()
    if len(list(active_count)) >= max_keys:
        raise HTTPException(
            status_code=403,
            detail=f"API key limit ({max_keys}) reached. Upgrade to Pro for more.",
        )

    # Generate key
    raw_secret = secrets.token_urlsafe(24)
    raw_key = f"{API_KEY_PREFIX}{raw_secret}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]

    api_key = ApiKey(
        user_id=user.id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        name=request.name,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        key=raw_key,
    )


@router.get("", response_model=list[ApiKeyResponse])
def list_api_keys(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all active API keys for the current user."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    keys = (
        db.execute(
            select(ApiKey)
            .where(ApiKey.user_id == user.id, ApiKey.is_active == True)  # noqa: E712
            .order_by(ApiKey.created_at.desc())
        )
        .scalars()
        .all()
    )

    return [
        ApiKeyResponse(
            id=k.id,
            key_prefix=k.key_prefix,
            name=k.name,
            last_used_at=k.last_used_at,
            is_active=k.is_active,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=204)
def revoke_api_key(
    key_id: int,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke (soft-delete) an API key."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    api_key = db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    ).scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    db.commit()
