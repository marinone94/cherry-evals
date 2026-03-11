"""Rate limiting and quota enforcement tests."""

from datetime import UTC, datetime, timedelta

import pytest

from api.deps import FREE_LIMITS, PRO_LIMITS, ULTRA_LIMITS, _rate_limit_buckets, effective_tier
from tests.conftest import _make_fake_user


@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    """Reset in-memory rate limit buckets between tests."""
    _rate_limit_buckets.clear()
    yield
    _rate_limit_buckets.clear()


class TestKeywordSearchRateLimit:
    """Per-minute rate limiting on keyword search."""

    def test_keyword_search_within_limit(self, authed_client_free):
        """Free user can search within the rate limit."""
        resp = authed_client_free.post("/search", json={"query": "test"})
        assert resp.status_code == 200


class TestSemanticSearchQuota:
    """Daily semantic search quota enforcement."""

    def test_semantic_search_quota_not_enforced_when_disabled(self, test_client):
        """Auth disabled: no quota enforcement."""
        # This might fail due to Qdrant not being available, which is expected
        # We just verify it doesn't fail with 429 (quota exceeded)
        resp = test_client.post(
            "/search/semantic",
            json={"query": "test", "limit": 5},
        )
        assert resp.status_code != 429


class TestTierLimits:
    """Verify tier limit constants are sensible."""

    def test_free_limits_are_restrictive(self):
        assert FREE_LIMITS["llm_calls_per_day"] == 0
        assert FREE_LIMITS["semantic_searches_per_day"] == 50
        assert FREE_LIMITS["max_collections"] == 10
        assert FREE_LIMITS["max_api_keys"] == 1

    def test_pro_limits_are_generous(self):
        assert PRO_LIMITS["llm_calls_per_day"] == 180
        assert PRO_LIMITS["semantic_searches_per_day"] == -1  # unlimited
        assert PRO_LIMITS["max_collections"] == -1  # unlimited
        assert PRO_LIMITS["max_api_keys"] == 10

    def test_ultra_limits(self):
        assert ULTRA_LIMITS["llm_calls_per_day"] == 300
        assert ULTRA_LIMITS["semantic_searches_per_day"] == -1  # unlimited
        assert ULTRA_LIMITS["max_collections"] == -1  # unlimited
        assert ULTRA_LIMITS["max_api_keys"] == 10

    def test_pro_rate_limit_higher_than_free(self):
        assert PRO_LIMITS["keyword_rpm"] > FREE_LIMITS["keyword_rpm"]

    def test_ultra_llm_limit_higher_than_pro(self):
        assert ULTRA_LIMITS["llm_calls_per_day"] > PRO_LIMITS["llm_calls_per_day"]


class TestEffectiveTier:
    """Test effective_tier() logic."""

    def test_free_user_no_trial(self):
        user = _make_fake_user(tier="free")
        assert effective_tier(user) == "free"

    def test_free_user_active_trial(self):
        user = _make_fake_user(tier="free", trial_ends_at=datetime.now(UTC) + timedelta(days=7))
        assert effective_tier(user) == "ultra"

    def test_free_user_expired_trial(self):
        user = _make_fake_user(tier="free", trial_ends_at=datetime.now(UTC) - timedelta(days=1))
        assert effective_tier(user) == "free"

    def test_pro_user_ignores_trial(self):
        user = _make_fake_user(
            tier="pro",
            supabase_id="pro-1",
            trial_ends_at=datetime.now(UTC) + timedelta(days=7),
        )
        assert effective_tier(user) == "pro"

    def test_ultra_user(self):
        user = _make_fake_user(tier="ultra", supabase_id="ultra-1")
        assert effective_tier(user) == "ultra"
