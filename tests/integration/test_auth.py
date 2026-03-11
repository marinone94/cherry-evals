"""Auth, authorization, and tier enforcement tests."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from cherry_evals.config import Settings
from db.postgres.base import get_db

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AUTH_ENABLED_SETTINGS = Settings(
    database_url="sqlite:///./test.db",
    qdrant_url="http://localhost:6333",
    google_api_key="test-api-key",
    cherry_data_dir=Path("./test_data"),
    auth_enabled=True,
    supabase_jwt_secret="test-secret",
)


@pytest.fixture
def unauthed_client(test_db_session):
    """Test client with auth_enabled=True but NO credentials."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Don't override get_current_user — let it run naturally

    with (
        patch("api.deps.settings", _AUTH_ENABLED_SETTINGS),
        patch("api.routes.export.settings", _AUTH_ENABLED_SETTINGS),
        patch("api.routes.collections.settings", _AUTH_ENABLED_SETTINGS),
        TestClient(app) as client,
    ):
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 401 on protected endpoints without auth
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """Endpoints that require auth should return 401 when no credentials."""

    def test_create_collection_requires_auth(self, unauthed_client):
        resp = unauthed_client.post("/collections", json={"name": "test"})
        assert resp.status_code == 401

    def test_list_collections_requires_auth(self, unauthed_client):
        resp = unauthed_client.get("/collections")
        assert resp.status_code == 401

    def test_create_api_key_requires_auth(self, unauthed_client):
        resp = unauthed_client.post("/api-keys", json={"name": "test"})
        assert resp.status_code == 401

    def test_list_api_keys_requires_auth(self, unauthed_client):
        resp = unauthed_client.get("/api-keys")
        assert resp.status_code == 401

    def test_account_me_requires_auth(self, unauthed_client):
        resp = unauthed_client.get("/account/me")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 403 on Pro endpoints with Free user
# ---------------------------------------------------------------------------


class TestFreeTierRestrictions:
    """Pro-only endpoints should return 403 for Free-tier users."""

    def test_intelligent_search_blocked_for_free(self, authed_client_free):
        resp = authed_client_free.post(
            "/search/intelligent",
            json={"query": "test", "limit": 5},
        )
        assert resp.status_code == 403

    def test_agent_discover_blocked_for_free(self, authed_client_free):
        resp = authed_client_free.post(
            "/agents/discover",
            json={"description": "test"},
        )
        assert resp.status_code == 403

    def test_agent_ingest_blocked_for_free(self, authed_client_free):
        resp = authed_client_free.post(
            "/agents/ingest",
            json={"description": "test"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Authenticated Free user can access basic endpoints
# ---------------------------------------------------------------------------


class TestFreeTierAccess:
    """Free users should be able to use basic endpoints."""

    def test_free_user_can_create_collection(self, authed_client_free):
        resp = authed_client_free.post(
            "/collections",
            json={"name": "My test collection"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My test collection"

    def test_free_user_can_list_collections(self, authed_client_free):
        resp = authed_client_free.get("/collections")
        assert resp.status_code == 200

    def test_free_user_can_keyword_search(self, authed_client_free):
        resp = authed_client_free.post(
            "/search",
            json={"query": "test"},
        )
        assert resp.status_code == 200

    def test_free_user_can_get_account(self, authed_client_free):
        resp = authed_client_free.get("/account/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "free"
        assert data["effective_tier"] == "free"
        assert data["email"] == "free@test.com"


# ---------------------------------------------------------------------------
# Public endpoints stay public
# ---------------------------------------------------------------------------


class TestPublicEndpoints:
    """Endpoints that should work without auth (health, facets, datasets)."""

    def test_health_no_auth(self, unauthed_client):
        resp = unauthed_client.get("/health")
        assert resp.status_code == 200

    def test_root_no_auth(self, unauthed_client):
        resp = unauthed_client.get("/")
        assert resp.status_code == 200

    def test_facets_no_auth(self, unauthed_client):
        """Facets endpoint doesn't require auth."""
        resp = unauthed_client.post("/search/facets", json={})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Existing tests still pass with auth_enabled=False
# ---------------------------------------------------------------------------


class TestAuthDisabledMode:
    """When auth_enabled=False, all endpoints work without credentials."""

    def test_collections_work_without_auth(self, test_client):
        resp = test_client.post("/collections", json={"name": "no-auth collection"})
        assert resp.status_code == 201

    def test_search_works_without_auth(self, test_client):
        resp = test_client.post("/search", json={"query": "test"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Polar webhook
# ---------------------------------------------------------------------------


class TestUltraTierAccess:
    """Ultra-tier users should access all paid endpoints."""

    def test_ultra_user_can_access_intelligent_search(self, authed_client_ultra):
        """Ultra user gets past the require_paid gate (may fail on LLM, but not 403)."""
        resp = authed_client_ultra.post(
            "/search/intelligent",
            json={"query": "test", "limit": 5},
        )
        # Should not be 403 (tier restriction)
        assert resp.status_code != 403

    def test_ultra_user_can_access_agents(self, authed_client_ultra):
        resp = authed_client_ultra.post(
            "/agents/discover",
            json={"description": "test"},
        )
        assert resp.status_code != 403

    def test_ultra_user_account_shows_ultra(self, authed_client_ultra):
        resp = authed_client_ultra.get("/account/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "ultra"
        assert data["effective_tier"] == "ultra"


# ---------------------------------------------------------------------------
# Trial user (free + active trial_ends_at) gets Ultra access
# ---------------------------------------------------------------------------


class TestTrialAccess:
    """Free users with active trial should get Ultra-level access."""

    def test_trial_user_can_access_intelligent_search(self, authed_client_trial):
        resp = authed_client_trial.post(
            "/search/intelligent",
            json={"query": "test", "limit": 5},
        )
        assert resp.status_code != 403

    def test_trial_user_can_access_agents(self, authed_client_trial):
        resp = authed_client_trial.post(
            "/agents/discover",
            json={"description": "test"},
        )
        assert resp.status_code != 403

    def test_trial_user_account_shows_effective_ultra(self, authed_client_trial):
        resp = authed_client_trial.get("/account/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "free"
        assert data["effective_tier"] == "ultra"
        assert data["trial_ends_at"] is not None


# ---------------------------------------------------------------------------
# Expired trial user falls back to Free limits
# ---------------------------------------------------------------------------


class TestExpiredTrialRestrictions:
    """Free users with expired trial should be blocked from paid features."""

    def test_expired_trial_blocked_from_intelligent_search(self, authed_client_expired_trial):
        resp = authed_client_expired_trial.post(
            "/search/intelligent",
            json={"query": "test", "limit": 5},
        )
        assert resp.status_code == 403

    def test_expired_trial_blocked_from_agents(self, authed_client_expired_trial):
        resp = authed_client_expired_trial.post(
            "/agents/discover",
            json={"description": "test"},
        )
        assert resp.status_code == 403

    def test_expired_trial_account_shows_free(self, authed_client_expired_trial):
        resp = authed_client_expired_trial.get("/account/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "free"
        assert data["effective_tier"] == "free"


# ---------------------------------------------------------------------------
# Polar webhook
# ---------------------------------------------------------------------------


class TestPolarWebhook:
    """Polar webhook signature verification and tier changes."""

    def test_webhook_rejects_bad_signature(self, unauthed_client):
        resp = unauthed_client.post(
            "/webhooks/polar",
            json={"type": "subscription.created", "data": {}},
            headers={"webhook-signature": "bad-signature"},
        )
        assert resp.status_code == 400
