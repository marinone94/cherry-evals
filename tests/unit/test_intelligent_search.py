"""Unit tests for the intelligent search pipeline.

All LLM calls (Google GenAI) are mocked — no real API calls are made.
"""

import json
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(example_id: int, question: str = "Q?", dataset: str = "MMLU") -> dict:
    """Build a minimal result dict matching the structure from search functions."""
    return {
        "id": example_id,
        "dataset_id": 1,
        "dataset_name": dataset,
        "question": question,
        "answer": "A",
        "choices": None,
        "example_metadata": {"subject": "math"},
        "score": 0.5,
    }


def _gemini_response(text: str) -> MagicMock:
    """Build a mock Gemini response object whose .text attribute returns text."""
    response = MagicMock()
    response.text = text
    return response


def _mock_settings_with_key() -> MagicMock:
    """Return a settings mock with a non-empty google_api_key."""
    mock_settings = MagicMock()
    mock_settings.google_api_key = "fake-api-key"
    return mock_settings


# ---------------------------------------------------------------------------
# parse_query tests
# ---------------------------------------------------------------------------


class TestParseQuery:
    """Tests for agents.query_agent.parse_query."""

    def test_returns_structured_params_on_success(self):
        """A valid Gemini response should be parsed into structured params."""
        payload = {
            "search_query": "hard science reasoning",
            "dataset": "ARC",
            "subject": None,
            "task_type": "science_qa",
            "explanation": "ARC contains science exam questions.",
        }
        mock_response = _gemini_response(json.dumps(payload))

        with (
            patch("agents.query_agent.settings", _mock_settings_with_key()),
            patch("agents.query_agent.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.query_agent import parse_query

            result = parse_query("hard science questions")

        assert result["search_query"] == "hard science reasoning"
        assert result["dataset"] == "ARC"
        assert result["task_type"] == "science_qa"
        assert result["subject"] is None
        assert "explanation" in result

    def test_returns_fallback_on_json_parse_error(self):
        """If Gemini returns invalid JSON, original query is used as fallback."""
        mock_response = _gemini_response("not valid json at all")

        with (
            patch("agents.query_agent.settings", _mock_settings_with_key()),
            patch("agents.query_agent.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.query_agent import parse_query

            result = parse_query("original query")

        assert result["search_query"] == "original query"
        assert result["dataset"] is None
        assert result["subject"] is None
        assert result["task_type"] is None

    def test_returns_fallback_on_llm_exception(self):
        """If Gemini raises an exception, original query is returned unchanged."""
        with (
            patch("agents.query_agent.settings", _mock_settings_with_key()),
            patch("agents.query_agent.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.side_effect = RuntimeError("API down")

            from agents.query_agent import parse_query

            result = parse_query("original query")

        assert result["search_query"] == "original query"
        assert result["dataset"] is None

    def test_returns_fallback_when_no_api_key(self):
        """Without a Google API key, the original query is returned unchanged."""
        with patch("agents.query_agent.settings") as mock_settings:
            mock_settings.google_api_key = ""

            from agents.query_agent import parse_query

            result = parse_query("my query")

        assert result["search_query"] == "my query"
        assert result["dataset"] is None

    def test_strips_markdown_fences_from_response(self):
        """Markdown code fences around JSON should be stripped before parsing."""
        payload = {
            "search_query": "python sort list",
            "dataset": "HumanEval",
            "subject": None,
            "task_type": "code_generation",
            "explanation": "HumanEval is for coding tasks.",
        }
        fenced = f"```json\n{json.dumps(payload)}\n```"
        mock_response = _gemini_response(fenced)

        with (
            patch("agents.query_agent.settings", _mock_settings_with_key()),
            patch("agents.query_agent.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.query_agent import parse_query

            result = parse_query("python sorting function")

        assert result["dataset"] == "HumanEval"
        assert result["task_type"] == "code_generation"

    def test_passes_available_datasets_in_prompt(self):
        """The model should be called with a prompt that includes dataset names."""
        payload = {
            "search_query": "cooking",
            "dataset": None,
            "subject": "cooking",
            "task_type": None,
            "explanation": "",
        }
        mock_response = _gemini_response(json.dumps(payload))

        with (
            patch("agents.query_agent.settings", _mock_settings_with_key()),
            patch("agents.query_agent.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.query_agent import parse_query

            parse_query("cooking", available_datasets=["MMLU", "HumanEval"])

        call_kwargs = mock_client.models.generate_content.call_args
        # contents argument should contain the dataset list
        contents = call_kwargs[1].get("contents") or call_kwargs[0][1]
        assert "MMLU" in contents
        assert "HumanEval" in contents

    def test_response_missing_search_query_falls_back(self):
        """If the response JSON has no search_query key, fall back gracefully."""
        payload = {"dataset": "GSM8K", "explanation": "Math"}
        mock_response = _gemini_response(json.dumps(payload))

        with (
            patch("agents.query_agent.settings", _mock_settings_with_key()),
            patch("agents.query_agent.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.query_agent import parse_query

            result = parse_query("fraction problems")

        assert result["search_query"] == "fraction problems"


# ---------------------------------------------------------------------------
# rerank_results tests
# ---------------------------------------------------------------------------


class TestRerankResults:
    """Tests for agents.reranker.rerank_results."""

    def test_returns_reordered_results(self):
        """A valid Gemini response should re-order the results by ranked_ids."""
        results = [_make_result(1), _make_result(2), _make_result(3)]
        rerank_payload = {
            "ranked_ids": [3, 1, 2],
            "explanation": "3 is most relevant",
        }
        mock_response = _gemini_response(json.dumps(rerank_payload))

        with (
            patch("agents.reranker.settings", _mock_settings_with_key()),
            patch("agents.reranker.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.reranker import rerank_results

            reranked = rerank_results("query", results, limit=3)

        ids = [r["id"] for r in reranked]
        assert ids == [3, 1, 2]

    def test_returns_original_order_on_llm_failure(self):
        """If Gemini raises an exception, original order is preserved."""
        results = [_make_result(1), _make_result(2), _make_result(3)]

        with (
            patch("agents.reranker.settings", _mock_settings_with_key()),
            patch("agents.reranker.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.side_effect = RuntimeError("API error")

            from agents.reranker import rerank_results

            reranked = rerank_results("query", results, limit=3)

        ids = [r["id"] for r in reranked]
        assert ids == [1, 2, 3]

    def test_returns_original_order_on_json_parse_error(self):
        """Invalid JSON from Gemini should return original order."""
        results = [_make_result(1), _make_result(2)]
        mock_response = _gemini_response("not json")

        with (
            patch("agents.reranker.settings", _mock_settings_with_key()),
            patch("agents.reranker.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.reranker import rerank_results

            reranked = rerank_results("query", results, limit=2)

        ids = [r["id"] for r in reranked]
        assert ids == [1, 2]

    def test_respects_limit(self):
        """Results should be truncated to limit after re-ranking."""
        results = [_make_result(i) for i in range(1, 6)]
        rerank_payload = {
            "ranked_ids": [5, 4, 3, 2, 1],
            "explanation": "reversed",
        }
        mock_response = _gemini_response(json.dumps(rerank_payload))

        with (
            patch("agents.reranker.settings", _mock_settings_with_key()),
            patch("agents.reranker.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.reranker import rerank_results

            reranked = rerank_results("query", results, limit=3)

        assert len(reranked) == 3
        assert reranked[0]["id"] == 5

    def test_returns_empty_list_for_empty_input(self):
        """Empty input should return empty list without calling the LLM."""
        with (
            patch("agents.reranker.settings", _mock_settings_with_key()),
            patch("agents.reranker.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            from agents.reranker import rerank_results

            result = rerank_results("query", [], limit=10)

        assert result == []
        mock_client.models.generate_content.assert_not_called()

    def test_returns_original_on_missing_api_key(self):
        """Without a Google API key, original order is returned."""
        results = [_make_result(1), _make_result(2)]

        with patch("agents.reranker.settings") as mock_settings:
            mock_settings.google_api_key = ""

            from agents.reranker import rerank_results

            reranked = rerank_results("query", results, limit=2)

        assert [r["id"] for r in reranked] == [1, 2]

    def test_appends_unranked_results(self):
        """Results not in ranked_ids should be appended at the end."""
        results = [_make_result(1), _make_result(2), _make_result(3)]
        rerank_payload = {
            "ranked_ids": [2],  # Only ranks one result
            "explanation": "partial ranking",
        }
        mock_response = _gemini_response(json.dumps(rerank_payload))

        with (
            patch("agents.reranker.settings", _mock_settings_with_key()),
            patch("agents.reranker.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            from agents.reranker import rerank_results

            reranked = rerank_results("query", results, limit=3)

        ids = [r["id"] for r in reranked]
        assert ids[0] == 2  # Ranked first
        assert set(ids) == {1, 2, 3}  # All present


# ---------------------------------------------------------------------------
# intelligent_search orchestrator tests
# ---------------------------------------------------------------------------


class TestIntelligentSearch:
    """Tests for core.search.intelligent.intelligent_search."""

    def _make_db_session(self) -> MagicMock:
        return MagicMock()

    def test_calls_parse_query_and_hybrid_search(self):
        """Orchestrator should call parse_query then hybrid_search."""
        results = [_make_result(1), _make_result(2)]
        parsed = {
            "search_query": "expanded query",
            "dataset": "MMLU",
            "subject": "math",
            "task_type": None,
            "explanation": "detected MMLU",
        }

        with (
            patch("core.search.intelligent.parse_query", return_value=parsed) as mock_parse,
            patch(
                "core.search.intelligent.hybrid_search", return_value=(results, 2)
            ) as mock_hybrid,
            patch("core.search.intelligent.rerank_results", return_value=results),
        ):
            from core.search.intelligent import intelligent_search

            out_results, total, metadata = intelligent_search(
                db=self._make_db_session(), query="math problems", limit=10
            )

        mock_parse.assert_called_once_with("math problems")
        mock_hybrid.assert_called_once()
        assert total == 2
        assert metadata["parsed"]["dataset"] == "MMLU"
        assert metadata["collection_searched"] == "mmlu_embeddings"

    def test_falls_back_to_keyword_when_hybrid_fails(self):
        """If hybrid_search raises, keyword_search should be used as fallback."""
        results = [_make_result(1)]
        parsed = {
            "search_query": "query",
            "dataset": None,
            "subject": None,
            "task_type": None,
            "explanation": "",
        }

        with (
            patch("core.search.intelligent.parse_query", return_value=parsed),
            patch(
                "core.search.intelligent.hybrid_search",
                side_effect=RuntimeError("Qdrant down"),
            ),
            patch("core.search.intelligent.keyword_search", return_value=(results, 1)) as mock_kw,
            patch("core.search.intelligent.rerank_results", return_value=results),
        ):
            from core.search.intelligent import intelligent_search

            out_results, total, metadata = intelligent_search(
                db=self._make_db_session(), query="query", limit=10
            )

        mock_kw.assert_called_once()
        assert total == 1

    def test_uses_caller_collection_when_provided(self):
        """Caller-supplied collection_name should override the inferred one."""
        results = [_make_result(1)]
        parsed = {
            "search_query": "query",
            "dataset": "MMLU",
            "subject": None,
            "task_type": None,
            "explanation": "",
        }

        with (
            patch("core.search.intelligent.parse_query", return_value=parsed),
            patch(
                "core.search.intelligent.hybrid_search", return_value=(results, 1)
            ) as mock_hybrid,
            patch("core.search.intelligent.rerank_results", return_value=results),
        ):
            from core.search.intelligent import intelligent_search

            _, _, metadata = intelligent_search(
                db=self._make_db_session(),
                query="query",
                limit=5,
                collection_name="custom_collection",
            )

        # The custom collection should be passed to hybrid_search
        call_kwargs = mock_hybrid.call_args[1]
        assert call_kwargs["collection_name"] == "custom_collection"
        assert metadata["collection_searched"] == "custom_collection"

    def test_metadata_contains_required_keys(self):
        """Metadata dict should contain all expected top-level keys."""
        results = [_make_result(1)]
        parsed = {
            "search_query": "q",
            "dataset": None,
            "subject": None,
            "task_type": None,
            "explanation": "",
        }

        with (
            patch("core.search.intelligent.parse_query", return_value=parsed),
            patch("core.search.intelligent.hybrid_search", return_value=(results, 1)),
            patch("core.search.intelligent.rerank_results", return_value=results),
        ):
            from core.search.intelligent import intelligent_search

            _, _, metadata = intelligent_search(db=self._make_db_session(), query="q", limit=5)

        assert "original_query" in metadata
        assert "parsed" in metadata
        assert "collection_searched" in metadata
        assert "reranking_applied" in metadata
        assert metadata["original_query"] == "q"

    def test_pagination_applied_after_reranking(self):
        """Pagination offset/limit should be applied to the re-ranked list."""
        all_results = [_make_result(i) for i in range(1, 6)]
        parsed = {
            "search_query": "q",
            "dataset": None,
            "subject": None,
            "task_type": None,
            "explanation": "",
        }

        with (
            patch("core.search.intelligent.parse_query", return_value=parsed),
            patch(
                "core.search.intelligent.hybrid_search",
                return_value=(all_results, 5),
            ),
            patch("core.search.intelligent.rerank_results", return_value=all_results),
        ):
            from core.search.intelligent import intelligent_search

            out_results, total, _ = intelligent_search(
                db=self._make_db_session(), query="q", limit=2, offset=1
            )

        assert len(out_results) == 2
        assert out_results[0]["id"] == 2  # Offset 1 skips first result
        assert total == 5


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestIntelligentSearchEndpoint:
    """Integration-style tests for POST /search/intelligent using mocked orchestrator."""

    def test_returns_200_with_valid_request(self, test_client):
        """The endpoint should return 200 and the expected response structure."""
        mock_results = [_make_result(1), _make_result(2)]
        mock_metadata = {
            "original_query": "hard math",
            "parsed": {
                "search_query": "hard mathematics problems",
                "dataset": "GSM8K",
                "subject": None,
                "task_type": "math_reasoning",
                "explanation": "GSM8K contains math word problems.",
            },
            "collection_searched": "gsm8k_embeddings",
            "reranking_applied": True,
        }

        with patch(
            "core.search.intelligent.intelligent_search",
            return_value=(mock_results, 2, mock_metadata),
        ):
            response = test_client.post(
                "/search/intelligent",
                json={"query": "hard math", "limit": 10, "strategy": "pipeline"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["query"] == "hard math"
        assert len(data["results"]) == 2
        assert "metadata" in data
        assert data["metadata"]["parsed"]["dataset"] == "GSM8K"

    def test_rejects_empty_query(self, test_client):
        """An empty query string should be rejected with 422."""
        response = test_client.post("/search/intelligent", json={"query": ""})
        assert response.status_code == 422

    def test_rejects_invalid_limit(self, test_client):
        """A limit greater than 100 should be rejected with 422."""
        response = test_client.post("/search/intelligent", json={"query": "test", "limit": 200})
        assert response.status_code == 422

    def test_returns_empty_results_gracefully(self, test_client):
        """Empty result list should return 200 with total=0."""
        empty_metadata = {
            "original_query": "x",
            "parsed": {},
            "collection_searched": "mmlu_embeddings",
            "reranking_applied": True,
        }
        with patch(
            "core.search.intelligent.intelligent_search",
            return_value=([], 0, empty_metadata),
        ):
            response = test_client.post(
                "/search/intelligent", json={"query": "x", "strategy": "pipeline"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_response_structure(self, test_client):
        """Response should contain all expected top-level fields."""
        mock_results = [_make_result(1)]
        mock_metadata = {
            "original_query": "q",
            "parsed": {
                "search_query": "q",
                "dataset": None,
                "subject": None,
                "task_type": None,
                "explanation": "",
            },
            "collection_searched": "mmlu_embeddings",
            "reranking_applied": True,
        }

        with patch(
            "core.search.intelligent.intelligent_search",
            return_value=(mock_results, 1, mock_metadata),
        ):
            response = test_client.post(
                "/search/intelligent", json={"query": "q", "strategy": "pipeline"}
            )

        assert response.status_code == 200
        data = response.json()
        for field in ("results", "total", "query", "offset", "limit", "metadata"):
            assert field in data, f"Missing field: {field}"

    def test_default_offset_and_limit(self, test_client):
        """Default offset=0 and limit=20 should be used when not specified."""
        with patch(
            "core.search.intelligent.intelligent_search",
            return_value=([], 0, {}),
        ):
            response = test_client.post(
                "/search/intelligent", json={"query": "test", "strategy": "pipeline"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 20
        assert data["offset"] == 0
