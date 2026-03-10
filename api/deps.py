"""Dependency injection for authentication, authorization, and rate limiting."""

import hashlib
import logging
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cherry_evals.config import settings
from db.postgres.base import get_db
from db.postgres.models import ApiKey, Collection, CollectionExample, User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier limit constants
# ---------------------------------------------------------------------------

FREE_LIMITS = {
    "keyword_rpm": 30,
    "semantic_searches_per_day": 50,
    "llm_calls_per_day": 0,  # blocked
    "max_collections": 10,
    "max_examples_per_collection": 1000,
    "max_api_keys": 1,
}

PRO_LIMITS = {
    "keyword_rpm": 120,
    "semantic_searches_per_day": -1,  # unlimited
    "llm_calls_per_day": 180,
    "max_collections": -1,  # unlimited
    "max_examples_per_collection": -1,  # unlimited
    "max_api_keys": 10,
}

ULTRA_LIMITS = {
    "keyword_rpm": 120,
    "semantic_searches_per_day": -1,  # unlimited
    "llm_calls_per_day": 300,  # 50 Pro + 250 Flash combined
    "max_collections": -1,  # unlimited
    "max_examples_per_collection": -1,  # unlimited
    "max_api_keys": 10,
}


def effective_tier(user: User) -> str:
    """Return the effective tier, accounting for active trials."""
    if user.tier == "free" and user.trial_ends_at and user.trial_ends_at > datetime.now(UTC):
        return "ultra"
    return user.tier


def _get_limits(user: User | None) -> dict:
    """Return tier limits for a user (or Free defaults for anonymous)."""
    if user is None:
        return FREE_LIMITS
    tier = effective_tier(user)
    if tier == "ultra":
        return ULTRA_LIMITS
    if tier == "pro":
        return PRO_LIMITS
    return FREE_LIMITS


# ---------------------------------------------------------------------------
# JWT verification (Supabase HS256)
# ---------------------------------------------------------------------------


def _decode_supabase_jwt(token: str) -> dict:
    """Decode and verify a Supabase JWT using PyJWT (HS256).

    Validates signature, expiry, audience, and not-before claims.
    Returns the JWT payload dict, or raises HTTPException on failure.
    """
    try:
        return pyjwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except pyjwt.InvalidTokenError as e:
        logger.warning("JWT decode failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token") from e


# ---------------------------------------------------------------------------
# User resolution helpers
# ---------------------------------------------------------------------------


def _provision_user(db: Session, supabase_id: str, email: str) -> User:
    """JIT provision a user on first authenticated request."""
    user = User(
        supabase_id=supabase_id,
        email=email,
        tier="free",
        trial_ends_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Provisioned new user: %s (%s)", supabase_id, email)
    return user


def _resolve_from_jwt(token: str, db: Session) -> User:
    """Resolve a User from a Bearer JWT."""
    payload = _decode_supabase_jwt(token)
    supabase_id = payload.get("sub")
    email = payload.get("email", "")
    if not supabase_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub")

    user = db.execute(select(User).where(User.supabase_id == supabase_id)).scalar_one_or_none()
    if not user:
        user = _provision_user(db, supabase_id, email)
    return user


def _resolve_from_api_key(raw_key: str, db: Session) -> User:
    """Resolve a User from an API key."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)  # noqa: E712
    ).scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Update last_used_at
    api_key.last_used_at = datetime.now(UTC)
    db.commit()

    return api_key.user


# ---------------------------------------------------------------------------
# Core auth dependencies
# ---------------------------------------------------------------------------


def get_optional_user(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """Resolve the current user from JWT or API key, or return None.

    When auth_enabled is False, always returns None (open access).
    """
    if not settings.auth_enabled:
        return None

    # Try Bearer JWT first
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        return _resolve_from_jwt(token, db)

    # Try API key
    if x_api_key:
        return _resolve_from_api_key(x_api_key, db)

    return None


def get_current_user(
    user: User | None = Depends(get_optional_user),
) -> User | None:
    """Require an authenticated user (401 if not authed).

    When auth_enabled is False, returns None to allow open access.
    """
    if not settings.auth_enabled:
        return None
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_paid(
    user: User | None = Depends(get_current_user),
) -> User | None:
    """Require a paid-tier user — Pro, Ultra, or active trial (403 if Free).

    When auth_enabled is False, returns None.
    """
    if not settings.auth_enabled:
        return None
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if effective_tier(user) not in ("pro", "ultra"):
        raise HTTPException(
            status_code=403, detail="This feature requires a Pro or Ultra subscription."
        )
    return user


# ---------------------------------------------------------------------------
# Rate limiting (in-memory per-minute burst limiter)
# ---------------------------------------------------------------------------

# {user_key: [(timestamp, ...)] }
_rate_limit_buckets: dict[str, list[float]] = defaultdict(list)


def _user_key(user: User | None, request: Request) -> str:
    """Generate a rate limit key — user ID or client IP.

    WARNING: This rate limiter is per-process and not shared across workers.
    For multi-worker deployments, use Redis-backed rate limiting.
    """
    if user and hasattr(user, "supabase_id"):
        return f"user:{user.supabase_id}"
    # Prefer X-Forwarded-For from trusted proxy over request.client.host
    forwarded = request.headers.get("x-forwarded-for", "")
    host = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else "unknown")
    )
    return f"ip:{host}"


def check_search_rate_limit(
    request: Request,
    user: User | None = Depends(get_optional_user),
):
    """Enforce per-minute rate limit on keyword search."""
    if not settings.auth_enabled:
        return

    limits = _get_limits(user)
    rpm = limits["keyword_rpm"]
    key = _user_key(user, request)

    now = time.time()
    window = now - 60
    bucket = _rate_limit_buckets[key]
    # Prune old entries
    _rate_limit_buckets[key] = [t for t in bucket if t > window]
    bucket = _rate_limit_buckets[key]

    if len(bucket) >= rpm:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

    bucket.append(now)


# ---------------------------------------------------------------------------
# Daily quota checks (PostgreSQL-backed, survives restarts)
# ---------------------------------------------------------------------------


def _maybe_reset_quotas(user: User, db: Session):
    """Reset daily counters if quota_reset_at is in the past."""
    now = datetime.now(UTC)
    if user.quota_reset_at <= now:
        user.llm_calls_today = 0
        user.semantic_searches_today = 0
        user.quota_reset_at = now + timedelta(days=1)
        db.commit()
        db.refresh(user)


def check_semantic_search_quota(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check and increment daily semantic search quota."""
    if not settings.auth_enabled or user is None:
        return

    _maybe_reset_quotas(user, db)
    limits = _get_limits(user)
    daily_limit = limits["semantic_searches_per_day"]

    if daily_limit != -1 and user.semantic_searches_today >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily semantic search limit ({daily_limit}) reached. "
            "Upgrade to Pro for unlimited.",
        )

    user.semantic_searches_today += 1
    db.commit()


def check_and_increment_llm_budget(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check and increment daily LLM call quota."""
    if not settings.auth_enabled or user is None:
        return

    _maybe_reset_quotas(user, db)
    limits = _get_limits(user)
    daily_limit = limits["llm_calls_per_day"]

    if daily_limit == 0:
        raise HTTPException(
            status_code=403,
            detail="LLM-powered features require a Pro subscription.",
        )

    if daily_limit != -1 and user.llm_calls_today >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily LLM call limit ({daily_limit}) reached.",
        )

    user.llm_calls_today += 1
    db.commit()


# ---------------------------------------------------------------------------
# Collection / example limit checks
# ---------------------------------------------------------------------------


def check_collection_limit(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check that Free users haven't exceeded their collection limit."""
    if not settings.auth_enabled or user is None:
        return

    limits = _get_limits(user)
    max_collections = limits["max_collections"]
    if max_collections == -1:
        return

    count = db.execute(
        select(func.count(Collection.id)).where(Collection.user_id == user.supabase_id)
    ).scalar()

    if count >= max_collections:
        raise HTTPException(
            status_code=403,
            detail=f"Collection limit ({max_collections}) reached. Upgrade to Pro for unlimited.",
        )


def check_collection_example_limit(
    collection_id: int,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check that Free users haven't exceeded per-collection example limit.

    Also verifies the collection exists and belongs to the current user.
    """
    if not settings.auth_enabled or user is None:
        return

    # Verify collection ownership before checking limits
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.user_id != user.supabase_id:
        raise HTTPException(status_code=404, detail="Collection not found")

    limits = _get_limits(user)
    max_examples = limits["max_examples_per_collection"]
    if max_examples == -1:
        return

    count = db.execute(
        select(func.count(CollectionExample.id)).where(
            CollectionExample.collection_id == collection_id
        )
    ).scalar()

    if count >= max_examples:
        raise HTTPException(
            status_code=403,
            detail=f"Example limit ({max_examples} per collection) reached. Upgrade to Pro.",
        )
