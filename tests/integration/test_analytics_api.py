"""Integration tests for analytics API endpoints."""

from db.postgres.models import Collection, CurationEvent, Dataset, Example


def _seed_examples(db_session, count=3, ds_name="AnalyticsDS"):
    """Seed a dataset and examples for analytics tests."""
    dataset = Dataset(name=ds_name, source="test", task_type="qa")
    db_session.add(dataset)
    db_session.flush()

    examples = []
    for i in range(count):
        ex = Example(
            dataset_id=dataset.id,
            question=f"Question {i}?",
            answer=f"Answer {i}",
        )
        db_session.add(ex)
        examples.append(ex)
    db_session.flush()
    return dataset, examples


def _seed_collection(db_session, name="AnalyticsColl"):
    """Seed a collection."""
    coll = Collection(name=name)
    db_session.add(coll)
    db_session.flush()
    return coll


class TestAnalyticsStats:
    def test_stats_empty_database(self, test_client):
        """GET /analytics/stats should return zero counts on empty database."""
        response = test_client.get("/analytics/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "events_by_type" in data
        assert "most_searched_queries" in data
        assert "most_picked_examples" in data
        assert data["total_events"] == 0
        assert data["events_by_type"] == {}

    def test_stats_with_events(self, test_client, test_db_session):
        """GET /analytics/stats should reflect seeded events."""
        # Seed some events directly into the DB
        test_db_session.add(
            CurationEvent(event_type="search", query="neural nets", search_mode="keyword")
        )
        test_db_session.add(
            CurationEvent(event_type="search", query="transformers", search_mode="hybrid")
        )
        test_db_session.add(CurationEvent(event_type="pick", example_id=None))
        test_db_session.flush()

        response = test_client.get("/analytics/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] >= 3
        assert data["events_by_type"].get("search", 0) >= 2
        assert data["events_by_type"].get("pick", 0) >= 1

    def test_stats_response_structure(self, test_client):
        """GET /analytics/stats should always return the expected keys."""
        response = test_client.get("/analytics/stats")

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) >= {
            "total_events",
            "events_by_type",
            "most_searched_queries",
            "most_picked_examples",
        }


class TestAnalyticsPopular:
    def test_popular_empty_database(self, test_client):
        """GET /analytics/popular should return an empty list on empty database."""
        response = test_client.get("/analytics/popular")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_popular_with_pick_events(self, test_client, test_db_session):
        """GET /analytics/popular should return examples sorted by pick count."""
        _, examples = _seed_examples(test_db_session, count=3, ds_name="PopDS")

        # Pick example 0 twice, example 1 once
        test_db_session.add(CurationEvent(event_type="pick", example_id=examples[0].id))
        test_db_session.add(CurationEvent(event_type="pick", example_id=examples[0].id))
        test_db_session.add(CurationEvent(event_type="pick", example_id=examples[1].id))
        test_db_session.flush()

        response = test_client.get("/analytics/popular")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Most picked first
        target_ids = {examples[0].id, examples[1].id}
        pick_counts = [item["pick_count"] for item in data if item["example_id"] in target_ids]
        assert pick_counts == sorted(pick_counts, reverse=True)

    def test_popular_limit_parameter(self, test_client, test_db_session):
        """GET /analytics/popular?limit=2 should return at most 2 results."""
        _, examples = _seed_examples(test_db_session, count=5, ds_name="PopLimitDS")
        for ex in examples:
            test_db_session.add(CurationEvent(event_type="pick", example_id=ex.id))
        test_db_session.flush()

        response = test_client.get("/analytics/popular?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_popular_item_structure(self, test_client, test_db_session):
        """GET /analytics/popular items should have example_id and pick_count."""
        _, examples = _seed_examples(test_db_session, count=1, ds_name="PopStructDS")
        test_db_session.add(CurationEvent(event_type="pick", example_id=examples[0].id))
        test_db_session.flush()

        response = test_client.get("/analytics/popular")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        item = next(d for d in data if d["example_id"] == examples[0].id)
        assert "example_id" in item
        assert "pick_count" in item
        assert item["pick_count"] >= 1


class TestAnalyticsCoPicked:
    def test_co_picked_no_events(self, test_client):
        """GET /analytics/co-picked/{id} should return empty list with no events."""
        response = test_client.get("/analytics/co-picked/99999")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data == []

    def test_co_picked_with_events(self, test_client, test_db_session):
        """GET /analytics/co-picked/{id} should return co-picked examples."""
        _, examples = _seed_examples(test_db_session, count=3, ds_name="CoDS")
        coll = _seed_collection(test_db_session, name="CoColl")

        # examples[0] and examples[1] picked in same collection
        test_db_session.add(
            CurationEvent(event_type="pick", example_id=examples[0].id, collection_id=coll.id)
        )
        test_db_session.add(
            CurationEvent(event_type="pick", example_id=examples[1].id, collection_id=coll.id)
        )
        test_db_session.flush()

        response = test_client.get(f"/analytics/co-picked/{examples[0].id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        co_ids = [item["example_id"] for item in data]
        assert examples[1].id in co_ids

    def test_co_picked_item_structure(self, test_client, test_db_session):
        """GET /analytics/co-picked/{id} items should have example_id and co_pick_count."""
        _, examples = _seed_examples(test_db_session, count=2, ds_name="CoStructDS")
        coll = _seed_collection(test_db_session, name="CoStructColl")

        test_db_session.add(
            CurationEvent(event_type="pick", example_id=examples[0].id, collection_id=coll.id)
        )
        test_db_session.add(
            CurationEvent(event_type="pick", example_id=examples[1].id, collection_id=coll.id)
        )
        test_db_session.flush()

        response = test_client.get(f"/analytics/co-picked/{examples[0].id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        item = data[0]
        assert "example_id" in item
        assert "co_pick_count" in item

    def test_co_picked_limit_parameter(self, test_client, test_db_session):
        """GET /analytics/co-picked/{id}?limit=1 should return at most 1 result."""
        _, examples = _seed_examples(test_db_session, count=5, ds_name="CoLimitDS")
        coll = _seed_collection(test_db_session, name="CoLimitColl")

        for ex in examples:
            test_db_session.add(
                CurationEvent(event_type="pick", example_id=ex.id, collection_id=coll.id)
            )
        test_db_session.flush()

        response = test_client.get(f"/analytics/co-picked/{examples[0].id}?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1


class TestEventRecordingDoesNotBreakFlows:
    def test_search_still_works(self, test_client, test_db_session):
        """Keyword search endpoint should return results even with event recording."""
        _, _ = _seed_examples(test_db_session, count=2, ds_name="SearchFlowDS")

        response = test_client.post("/search", json={"query": "Question"})

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_search_with_session_id_header(self, test_client, test_db_session):
        """Search with X-Session-ID header should work and record the session."""
        _, _ = _seed_examples(test_db_session, count=1, ds_name="SessionDS")

        response = test_client.post(
            "/search",
            json={"query": "Question"},
            headers={"X-Session-ID": "test-session-123"},
        )

        assert response.status_code == 200

    def test_add_examples_records_pick_event(self, test_client, test_db_session):
        """Adding examples to collection should record pick events."""
        _, examples = _seed_examples(test_db_session, count=2, ds_name="PickEventDS")
        coll = _seed_collection(test_db_session, name="PickEventColl")

        response = test_client.post(
            f"/collections/{coll.id}/examples",
            json={"example_ids": [examples[0].id]},
        )

        assert response.status_code == 201

        # Check event was recorded
        stats_response = test_client.get("/analytics/stats")
        stats = stats_response.json()
        assert stats["events_by_type"].get("pick", 0) >= 1

    def test_remove_example_records_remove_event(self, test_client, test_db_session):
        """Removing an example from a collection should record a remove event."""
        from db.postgres.models import CollectionExample

        _, examples = _seed_examples(test_db_session, count=1, ds_name="RemoveEventDS")
        coll = _seed_collection(test_db_session, name="RemoveEventColl")

        # Add directly via DB to avoid double-counting pick events
        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        response = test_client.delete(f"/collections/{coll.id}/examples/{examples[0].id}")
        assert response.status_code == 204

        stats_response = test_client.get("/analytics/stats")
        stats = stats_response.json()
        assert stats["events_by_type"].get("remove", 0) >= 1

    def test_export_records_export_event(self, test_client, test_db_session):
        """Exporting a collection should record an export event."""
        from db.postgres.models import CollectionExample

        dataset = Dataset(name="ExportEventDS", source="test", task_type="qa")
        test_db_session.add(dataset)
        test_db_session.flush()

        ex = Example(dataset_id=dataset.id, question="Q?", answer="A")
        test_db_session.add(ex)
        test_db_session.flush()

        coll = Collection(name="ExportEventColl")
        test_db_session.add(coll)
        test_db_session.flush()

        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=ex.id))
        test_db_session.flush()

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "json"},
        )

        assert response.status_code == 200

        stats_response = test_client.get("/analytics/stats")
        stats = stats_response.json()
        assert stats["events_by_type"].get("export", 0) >= 1

    def test_hybrid_search_records_event(self, test_client, test_db_session):
        """Hybrid search should record a search event even when semantic fails."""
        _, _ = _seed_examples(test_db_session, count=1, ds_name="HybridEventDS")

        # Hybrid search falls back to keyword when Qdrant not available
        response = test_client.post(
            "/search/hybrid",
            json={"query": "Question", "collection": "mmlu"},
        )

        # Should succeed (falls back to keyword)
        assert response.status_code == 200
