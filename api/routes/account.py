"""Account and usage endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import _get_limits, effective_tier, get_current_user
from db.postgres.base import get_db
from db.postgres.models import ApiKey, Collection, CollectionExample, CurationEvent, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])


class UsageStats(BaseModel):
    """Current usage counters and limits."""

    llm_calls_today: int
    llm_calls_limit: int  # -1 = unlimited, 0 = blocked
    semantic_searches_today: int
    semantic_searches_limit: int  # -1 = unlimited
    quota_resets_at: datetime


class AccountResponse(BaseModel):
    """User profile + usage."""

    email: str
    tier: str
    effective_tier: str
    trial_ends_at: datetime | None
    subscription_status: str | None
    usage: UsageStats
    created_at: datetime


@router.get("/me", response_model=AccountResponse)
def get_account(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return current user profile and usage stats."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    limits = _get_limits(user)

    return AccountResponse(
        email=user.email,
        tier=user.tier,
        effective_tier=effective_tier(user),
        trial_ends_at=user.trial_ends_at,
        subscription_status=user.subscription_status,
        usage=UsageStats(
            llm_calls_today=user.llm_calls_today,
            llm_calls_limit=limits["llm_calls_per_day"],
            semantic_searches_today=user.semantic_searches_today,
            semantic_searches_limit=limits["semantic_searches_per_day"],
            quota_resets_at=user.quota_reset_at,
        ),
        created_at=user.created_at,
    )


@router.get("/export")
def export_account_data(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GDPR Article 20 — data portability. Returns all user data as JSON."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Collections
    collections = (
        db.execute(select(Collection).where(Collection.user_id == user.supabase_id)).scalars().all()
    )
    collections_data = []
    for coll in collections:
        example_ids = (
            db.execute(
                select(CollectionExample.example_id).where(
                    CollectionExample.collection_id == coll.id
                )
            )
            .scalars()
            .all()
        )
        collections_data.append(
            {
                "id": coll.id,
                "name": coll.name,
                "description": coll.description,
                "example_ids": list(example_ids),
                "created_at": coll.created_at.isoformat(),
            }
        )

    # API keys (prefix only, never the hash)
    api_keys = db.execute(select(ApiKey).where(ApiKey.user_id == user.id)).scalars().all()
    keys_data = [
        {"prefix": k.key_prefix, "name": k.name, "created_at": k.created_at.isoformat()}
        for k in api_keys
    ]

    # Curation events
    events = (
        db.execute(
            select(CurationEvent)
            .where(CurationEvent.user_id == user.supabase_id)
            .order_by(CurationEvent.created_at.desc())
            .limit(10000)
        )
        .scalars()
        .all()
    )
    events_data = [
        {
            "event_type": ev.event_type,
            "query": ev.query,
            "example_id": ev.example_id,
            "collection_id": ev.collection_id,
            "created_at": ev.created_at.isoformat(),
        }
        for ev in events
    ]

    return JSONResponse(
        content={
            "account": {
                "email": user.email,
                "tier": user.tier,
                "created_at": user.created_at.isoformat(),
                "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
            },
            "collections": collections_data,
            "api_keys": keys_data,
            "curation_events": events_data,
        }
    )


@router.delete("/me", status_code=204)
def delete_account(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GDPR Article 17 — right to erasure. Deletes the user and all associated data.

    Cascade deletes: API keys (via ORM cascade), collections (via user_id match),
    and anonymises curation events (sets user_id to NULL).
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Anonymise curation events (preserve aggregated data, remove PII)
    db.execute(
        CurationEvent.__table__.update()
        .where(CurationEvent.user_id == user.supabase_id)
        .values(user_id=None, session_id=None)
    )

    # Delete user's collections (cascade removes collection_examples)
    collections = (
        db.execute(select(Collection).where(Collection.user_id == user.supabase_id)).scalars().all()
    )
    for coll in collections:
        db.delete(coll)

    # Delete user (cascade removes api_keys via ORM relationship)
    db.delete(user)
    db.commit()
    logger.info("Deleted account for user %s", user.supabase_id)
