"""Unit tests for MCP server authentication and user-scoped collection access.

Covers:
- _resolve_user_from_api_key: valid / invalid / inactive keys
- list_collections: scoped to user when _current_user is set
- create_collection: user_id stamped when _current_user is set
- add_to_collection / get_collection / export_collection: ownership enforcement
- stdio mode (no user): full access preserved
"""

import hashlib
import json

import pytest

from db.postgres.models import ApiKey, Collection, CollectionExample, Dataset, Example, User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _make_user(db, supabase_id: str = "user-abc") -> User:
    user = User(
        supabase_id=supabase_id,
        email=f"{supabase_id}@test.com",
        tier="free",
    )
    db.add(user)
    db.flush()
    return user


def _make_api_key(db, user: User, raw_key: str = "ck_live_testkey123") -> ApiKey:
    api_key = ApiKey(
        user_id=user.id,
        key_prefix=raw_key[:8],
        key_hash=_hash(raw_key),
        name="Test Key",
        is_active=True,
    )
    db.add(api_key)
    db.flush()
    return api_key


# ---------------------------------------------------------------------------
# Fixture: patch _get_db to use test session
# ---------------------------------------------------------------------------


@pytest.fixture
def _patch_session(test_db_session, monkeypatch):
    monkeypatch.setattr("mcp_server.server._get_db", lambda: test_db_session)


@pytest.fixture
def seeded_db(test_db_session):
    """Seed dataset + examples."""
    ds = Dataset(name="AuthTestDS", source="test", task_type="qa")
    test_db_session.add(ds)
    test_db_session.flush()

    examples = []
    for i in range(3):
        ex = Example(
            dataset_id=ds.id,
            question=f"Q{i}",
            answer=f"A{i}",
        )
        test_db_session.add(ex)
        examples.append(ex)
    test_db_session.flush()
    return ds, examples


# ---------------------------------------------------------------------------
# _resolve_user_from_api_key
# ---------------------------------------------------------------------------


class TestResolveUserFromApiKey:
    def test_valid_key_returns_user(self, test_db_session):
        from mcp_server.server import _resolve_user_from_api_key

        user = _make_user(test_db_session)
        raw = "ck_live_valid001"
        _make_api_key(test_db_session, user, raw)

        result = _resolve_user_from_api_key(raw, test_db_session)
        assert result is not None
        assert result.supabase_id == user.supabase_id

    def test_invalid_key_returns_none(self, test_db_session):
        from mcp_server.server import _resolve_user_from_api_key

        result = _resolve_user_from_api_key("ck_live_nonexistent", test_db_session)
        assert result is None

    def test_inactive_key_returns_none(self, test_db_session):
        from mcp_server.server import _resolve_user_from_api_key

        user = _make_user(test_db_session, supabase_id="user-inactive")
        raw = "ck_live_inactive"
        api_key = _make_api_key(test_db_session, user, raw)
        api_key.is_active = False
        test_db_session.flush()

        result = _resolve_user_from_api_key(raw, test_db_session)
        assert result is None

    def test_wrong_hash_returns_none(self, test_db_session):
        from mcp_server.server import _resolve_user_from_api_key

        user = _make_user(test_db_session, supabase_id="user-hash")
        raw = "ck_live_hashtest"
        _make_api_key(test_db_session, user, raw)

        result = _resolve_user_from_api_key("ck_live_wrongkey", test_db_session)
        assert result is None


# ---------------------------------------------------------------------------
# list_collections — user scoping
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_session")
class TestListCollectionsScoping:
    def test_stdio_mode_sees_all_collections(self, test_db_session):
        """When no user is set (stdio), all collections are returned."""
        import mcp_server.server as srv

        user_a = _make_user(test_db_session, supabase_id="user-a-list")
        user_b = _make_user(test_db_session, supabase_id="user-b-list")

        test_db_session.add(Collection(name="CollA", user_id=user_a.supabase_id))
        test_db_session.add(Collection(name="CollB", user_id=user_b.supabase_id))
        test_db_session.add(Collection(name="CollNone", user_id=None))
        test_db_session.flush()

        token = srv._current_user.set(None)
        try:
            result = json.loads(srv.list_collections())
        finally:
            srv._current_user.reset(token)

        names = [c["name"] for c in result]
        assert "CollA" in names
        assert "CollB" in names
        assert "CollNone" in names

    def test_http_mode_sees_only_own_collections(self, test_db_session):
        """When _current_user is set, only that user's collections are returned."""
        import mcp_server.server as srv

        user_a = _make_user(test_db_session, supabase_id="user-a-scope")
        user_b = _make_user(test_db_session, supabase_id="user-b-scope")

        test_db_session.add(Collection(name="MyCollA", user_id=user_a.supabase_id))
        test_db_session.add(Collection(name="OtherCollB", user_id=user_b.supabase_id))
        test_db_session.flush()

        token = srv._current_user.set(user_a)
        try:
            result = json.loads(srv.list_collections())
        finally:
            srv._current_user.reset(token)

        names = [c["name"] for c in result]
        assert "MyCollA" in names
        assert "OtherCollB" not in names


# ---------------------------------------------------------------------------
# create_collection — user_id stamping
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_session")
class TestCreateCollectionScoping:
    def test_creates_with_user_id_in_http_mode(self, test_db_session):
        from sqlalchemy import select

        import mcp_server.server as srv

        user = _make_user(test_db_session, supabase_id="user-create")
        supabase_id = user.supabase_id  # capture before session boundary

        token = srv._current_user.set(user)
        try:
            result = json.loads(srv.create_collection("AuthedColl"))
        finally:
            srv._current_user.reset(token)

        assert result["name"] == "AuthedColl"
        coll_id = result["id"]
        # Re-query from test session (create_collection commits on its own session)
        coll = test_db_session.execute(
            select(Collection).where(Collection.id == coll_id)
        ).scalar_one_or_none()
        assert coll is not None
        assert coll.user_id == supabase_id

    def test_creates_with_null_user_id_in_stdio_mode(self, test_db_session):
        import mcp_server.server as srv

        token = srv._current_user.set(None)
        try:
            result = json.loads(srv.create_collection("StdioColl"))
        finally:
            srv._current_user.reset(token)

        coll_id = result["id"]
        coll = test_db_session.get(Collection, coll_id)
        assert coll is not None
        assert coll.user_id is None


# ---------------------------------------------------------------------------
# add_to_collection — ownership enforcement
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_session")
class TestAddToCollectionOwnership:
    def test_owner_can_add(self, seeded_db, test_db_session):
        import mcp_server.server as srv

        _, examples = seeded_db
        user = _make_user(test_db_session, supabase_id="user-add-owner")
        coll = Collection(name="OwnedColl", user_id=user.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()

        token = srv._current_user.set(user)
        try:
            result = json.loads(srv.add_to_collection(coll.id, [examples[0].id]))
        finally:
            srv._current_user.reset(token)

        assert result["added"] == 1

    def test_other_user_cannot_add(self, seeded_db, test_db_session):
        import mcp_server.server as srv

        _, examples = seeded_db
        owner = _make_user(test_db_session, supabase_id="user-add-owner2")
        attacker = _make_user(test_db_session, supabase_id="user-add-attacker")
        coll = Collection(name="OwnerColl2", user_id=owner.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()

        token = srv._current_user.set(attacker)
        try:
            result = json.loads(srv.add_to_collection(coll.id, [examples[0].id]))
        finally:
            srv._current_user.reset(token)

        assert "error" in result

    def test_stdio_mode_can_add_to_any_collection(self, seeded_db, test_db_session):
        import mcp_server.server as srv

        _, examples = seeded_db
        owner = _make_user(test_db_session, supabase_id="user-add-owner3")
        coll = Collection(name="AnyAccessColl", user_id=owner.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()

        token = srv._current_user.set(None)
        try:
            result = json.loads(srv.add_to_collection(coll.id, [examples[0].id]))
        finally:
            srv._current_user.reset(token)

        assert result["added"] == 1


# ---------------------------------------------------------------------------
# get_collection — ownership enforcement
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_session")
class TestGetCollectionOwnership:
    def test_owner_can_get(self, seeded_db, test_db_session):
        import mcp_server.server as srv

        _, examples = seeded_db
        user = _make_user(test_db_session, supabase_id="user-get-owner")
        coll = Collection(name="GetOwnedColl", user_id=user.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()
        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        token = srv._current_user.set(user)
        try:
            result = json.loads(srv.get_collection(coll.id))
        finally:
            srv._current_user.reset(token)

        assert result["name"] == "GetOwnedColl"
        assert result["example_count"] == 1

    def test_other_user_cannot_get(self, test_db_session):
        import mcp_server.server as srv

        owner = _make_user(test_db_session, supabase_id="user-get-owner2")
        attacker = _make_user(test_db_session, supabase_id="user-get-attacker")
        coll = Collection(name="GetProtectedColl", user_id=owner.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()

        token = srv._current_user.set(attacker)
        try:
            result = json.loads(srv.get_collection(coll.id))
        finally:
            srv._current_user.reset(token)

        assert "error" in result

    def test_stdio_mode_can_get_any_collection(self, seeded_db, test_db_session):
        import mcp_server.server as srv

        _, examples = seeded_db
        owner = _make_user(test_db_session, supabase_id="user-get-owner3")
        coll = Collection(name="GetAnyAccessColl", user_id=owner.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()
        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        token = srv._current_user.set(None)
        try:
            result = json.loads(srv.get_collection(coll.id))
        finally:
            srv._current_user.reset(token)

        assert result["name"] == "GetAnyAccessColl"


# ---------------------------------------------------------------------------
# export_collection — ownership enforcement
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_session")
class TestExportCollectionOwnership:
    def test_owner_can_export(self, seeded_db, test_db_session):
        import mcp_server.server as srv

        _, examples = seeded_db
        user = _make_user(test_db_session, supabase_id="user-export-owner")
        coll = Collection(name="ExportOwnedColl", user_id=user.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()
        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        token = srv._current_user.set(user)
        try:
            result = srv.export_collection(coll.id, format="json")
        finally:
            srv._current_user.reset(token)

        # Valid JSON array (not an error)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_other_user_cannot_export(self, test_db_session):
        import mcp_server.server as srv

        owner = _make_user(test_db_session, supabase_id="user-export-owner2")
        attacker = _make_user(test_db_session, supabase_id="user-export-attacker")
        coll = Collection(name="ExportProtectedColl", user_id=owner.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()

        token = srv._current_user.set(attacker)
        try:
            result = json.loads(srv.export_collection(coll.id, format="json"))
        finally:
            srv._current_user.reset(token)

        assert "error" in result

    def test_stdio_mode_can_export_any_collection(self, seeded_db, test_db_session):
        import mcp_server.server as srv

        _, examples = seeded_db
        owner = _make_user(test_db_session, supabase_id="user-export-owner3")
        coll = Collection(name="ExportAnyAccessColl", user_id=owner.supabase_id)
        test_db_session.add(coll)
        test_db_session.flush()
        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        token = srv._current_user.set(None)
        try:
            result = srv.export_collection(coll.id, format="jsonl")
        finally:
            srv._current_user.reset(token)

        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert "question" in json.loads(lines[0])
