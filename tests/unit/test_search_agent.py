"""Unit tests for the autonomous SearchAgent.

All LLM calls and search functions are mocked — no real API or DB calls.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

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


def _make_db() -> MagicMock:
    return MagicMock()


def _gemini_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


def _plan_json(
    tool: str = "hybrid_search",
    search_query: str = "test query",
    dataset: str | None = None,
    subject: str | None = None,
) -> str:
    return json.dumps(
        {
            "tool": tool,
            "search_query": search_query,
            "dataset": dataset,
            "subject": subject,
            "rationale": "test",
        }
    )


def _eval_json(
    score: int = 8,
    should_continue: bool = False,
    refined: str | None = None,
    suggested_tool: str | None = None,
) -> str:
    return json.dumps(
        {
            "relevance_score": score,
            "assessment": "test assessment",
            "should_continue": should_continue,
            "refined_query": refined,
            "suggested_tool": suggested_tool,
            "suggested_dataset": None,
            "suggested_subject": None,
        }
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings_with_key():
    """Settings mock with a non-empty google_api_key."""
    mock = MagicMock()
    mock.google_api_key = "fake-key"
    return mock


# ---------------------------------------------------------------------------
# SearchAgent basic loop tests
# ---------------------------------------------------------------------------


class TestSearchAgentBasicLoop:
    """Tests for the agent's core search loop."""

    def test_returns_results_on_first_iteration(self, mock_settings_with_key):
        """Agent should return results immediately when evaluator is satisfied."""
        results = [_make_result(1), _make_result(2)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", return_value=(results, 2)),
            patch("agents.search_agent.keyword_search", return_value=(results, 2)),
        ):
            from agents.search_agent import SearchAgent

            # Patch the Gemini client to return plan then evaluation responses in order
            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(search_query="math problems"),  # planner
                    _eval_json(score=9, should_continue=False),  # evaluator
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("math problems", limit=10)

        assert len(result.results) == 2
        assert result.total == 2
        assert len(result.iterations) == 1
        assert result.iterations[0].tool_used == "hybrid_search"

    def test_iterates_when_evaluator_says_continue(self, mock_settings_with_key):
        """Agent should run a second iteration when evaluator requests it."""
        first_results = [_make_result(1)]
        second_results = [_make_result(2), _make_result(3)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch(
                "agents.search_agent.hybrid_search",
                side_effect=[
                    (first_results, 1),
                    (second_results, 2),
                ],
            ),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(search_query="q1"),  # planner
                    _eval_json(
                        score=3,
                        should_continue=True,
                        refined="q2 refined",
                        suggested_tool="hybrid_search",
                    ),  # eval iter 1
                    _eval_json(score=8, should_continue=False),  # eval iter 2
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("q1", limit=10)

        assert len(result.iterations) == 2
        assert result.iterations[0].query == "q1"
        assert result.iterations[1].query == "q2 refined"

    def test_stops_at_max_iterations(self, mock_settings_with_key):
        """Agent must stop after max_iterations regardless of evaluator output."""
        always_continue_eval = _eval_json(
            score=2, should_continue=True, refined="refined", suggested_tool="hybrid_search"
        )
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                # planner + 3 evaluations = 4 calls total for max_iterations=3
                mock_llm.side_effect = [
                    _plan_json(),
                    always_continue_eval,
                    always_continue_eval,
                    always_continue_eval,
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=10)

        assert len(result.iterations) == 3

    def test_max_iterations_clamped_to_5(self):
        """max_iterations > 5 should be silently clamped to 5."""
        from agents.search_agent import SearchAgent

        agent = SearchAgent(db=_make_db(), max_iterations=99)
        assert agent.max_iterations == 5

    def test_max_iterations_minimum_is_1(self):
        """max_iterations < 1 should be silently clamped to 1."""
        from agents.search_agent import SearchAgent

        agent = SearchAgent(db=_make_db(), max_iterations=0)
        assert agent.max_iterations == 1


# ---------------------------------------------------------------------------
# Combining results across iterations + deduplication
# ---------------------------------------------------------------------------


class TestDeduplication:
    """Tests for result merging and deduplication across iterations."""

    def test_deduplicates_results_across_iterations(self, mock_settings_with_key):
        """Results seen in multiple iterations should appear only once."""
        # Both iterations return the same result id=1 plus a unique id
        iteration1_results = [_make_result(1), _make_result(2)]
        iteration2_results = [_make_result(1), _make_result(3)]  # id=1 duplicated

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch(
                "agents.search_agent.hybrid_search",
                side_effect=[
                    (iteration1_results, 2),
                    (iteration2_results, 2),
                ],
            ),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(),
                    _eval_json(
                        score=4,
                        should_continue=True,
                        refined="refined",
                        suggested_tool="hybrid_search",
                    ),
                    _eval_json(score=9, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=20)

        ids = [r["id"] for r in result.results]
        # id=1 should appear only once
        assert ids.count(1) == 1
        # Should have 3 unique results: 1, 2, 3
        assert set(ids) == {1, 2, 3}
        assert result.total == 3

    def test_combines_results_from_multiple_iterations(self, mock_settings_with_key):
        """Total result count should reflect combined unique results."""
        results_a = [_make_result(i) for i in range(1, 4)]
        results_b = [_make_result(i) for i in range(4, 7)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch(
                "agents.search_agent.hybrid_search",
                side_effect=[(results_a, 3), (results_b, 3)],
            ),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(),
                    _eval_json(
                        score=3,
                        should_continue=True,
                        refined="more",
                        suggested_tool="hybrid_search",
                    ),
                    _eval_json(score=9, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=20)

        assert result.total == 6
        assert len(result.results) == 6

    def test_pagination_applied_to_combined_results(self, mock_settings_with_key):
        """Limit should be applied to the final combined result set."""
        results = [_make_result(i) for i in range(1, 11)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", return_value=(results, 10)),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(),
                    _eval_json(score=9, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=5)

        assert len(result.results) == 5
        assert result.total == 10


# ---------------------------------------------------------------------------
# LLM failure / graceful degradation
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """Tests for graceful degradation when LLM calls fail."""

    def test_falls_back_when_planner_llm_fails(self):
        """If the planner LLM call fails, agent uses hybrid_search with the raw query."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings") as mock_settings,
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            mock_settings.google_api_key = "fake"

            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini", return_value=None):
                agent = SearchAgent(db=_make_db(), max_iterations=1)
                result = agent.search("my query", limit=10)

        assert len(result.results) == 1
        assert result.iterations[0].tool_used == "hybrid_search"
        assert result.iterations[0].query == "my query"

    def test_falls_back_when_evaluator_llm_fails(self):
        """If evaluator LLM call fails, agent stops (should_continue=False by default)."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings") as mock_settings,
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            mock_settings.google_api_key = "fake"

            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                # planner succeeds, evaluator returns None (failure)
                mock_llm.side_effect = [_plan_json(), None]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=10)

        # Should stop after first iteration because default evaluation says stop
        assert len(result.iterations) == 1
        assert len(result.results) == 1

    def test_falls_back_when_evaluator_returns_invalid_json(self):
        """Invalid JSON from evaluator should cause agent to stop gracefully."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings") as mock_settings,
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            mock_settings.google_api_key = "fake"

            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [_plan_json(), "not valid json"]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=10)

        assert len(result.iterations) == 1

    def test_falls_back_when_no_api_key(self):
        """Without an API key, agent uses hybrid_search with raw query and stops."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings") as mock_settings,
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            mock_settings.google_api_key = ""  # no key

            from agents.search_agent import SearchAgent

            agent = SearchAgent(db=_make_db(), max_iterations=3)
            result = agent.search("query", limit=10)

        # Only one iteration: evaluator with empty results returns should_continue=False
        # (results = 1 item, so conservative evaluation => should_continue=False)
        assert len(result.results) >= 1

    def test_falls_back_to_keyword_when_hybrid_fails(self, mock_settings_with_key):
        """When hybrid_search fails, _hybrid_search wrapper falls back to keyword."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", side_effect=RuntimeError("Qdrant down")),
            patch("agents.search_agent.keyword_search", return_value=(results, 1)),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(tool="hybrid_search"),
                    _eval_json(score=7, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=1)
                result = agent.search("query", limit=10)

        # Should have results from keyword fallback
        assert len(result.results) == 1

    def test_returns_empty_when_all_searches_fail(self, mock_settings_with_key):
        """When all search tools fail and return empty, agent returns empty results."""
        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", side_effect=RuntimeError("all down")),
            patch("agents.search_agent.keyword_search", side_effect=RuntimeError("all down")),
        ):
            from agents.search_agent import SearchAgent

            cont_eval = _eval_json(
                score=0,
                should_continue=True,
                refined="r",
                suggested_tool="keyword_search",
            )
            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(tool="hybrid_search"),
                    cont_eval,
                    cont_eval,
                    _eval_json(score=0, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=10)

        assert result.results == []
        assert result.total == 0


# ---------------------------------------------------------------------------
# Tool selection
# ---------------------------------------------------------------------------


class TestToolSelection:
    """Tests for the agent's tool selection from planner output."""

    def test_uses_keyword_search_when_planner_says_so(self, mock_settings_with_key):
        """Agent should call keyword_search when the planner selects it."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.keyword_search", return_value=(results, 1)) as mock_kw,
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)) as mock_hybrid,
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(tool="keyword_search", search_query="exact term"),
                    _eval_json(score=8, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=1)
                agent.search("exact term", limit=10)

        mock_kw.assert_called_once()
        mock_hybrid.assert_not_called()

    def test_uses_semantic_search_when_planner_says_so(self, mock_settings_with_key):
        """Agent should call semantic_search when the planner selects it."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.semantic_search", return_value=results) as mock_sem,
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)) as mock_hybrid,
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(tool="semantic_search", search_query="conceptual ideas"),
                    _eval_json(score=8, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=1)
                agent.search("conceptual ideas", limit=10)

        mock_sem.assert_called_once()
        mock_hybrid.assert_not_called()

    def test_falls_back_to_hybrid_on_unknown_tool(self, mock_settings_with_key):
        """An unknown tool name from the planner should fall back to hybrid_search."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)) as mock_hybrid,
        ):
            from agents.search_agent import SearchAgent

            bad_plan = json.dumps(
                {
                    "tool": "nonexistent_tool",
                    "search_query": "q",
                    "dataset": None,
                    "subject": None,
                    "rationale": "",
                }
            )
            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    bad_plan,
                    _eval_json(score=8, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=1)
                agent.search("q", limit=10)

        mock_hybrid.assert_called_once()


# ---------------------------------------------------------------------------
# Iteration trace / AgentSearchResult structure
# ---------------------------------------------------------------------------


class TestAgentSearchResultStructure:
    """Tests for the iteration trace and metadata in AgentSearchResult."""

    def test_iterations_record_correct_tool_and_query(self, mock_settings_with_key):
        """Each iteration should record the tool and query that was used."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(tool="hybrid_search", search_query="expanded query"),
                    _eval_json(score=9, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("my query", limit=10)

        assert len(result.iterations) == 1
        it = result.iterations[0]
        assert it.tool_used == "hybrid_search"
        assert it.query == "expanded query"
        assert it.result_count == 1
        assert it.evaluation is not None
        assert "9" in it.evaluation  # score should appear in evaluation string

    def test_query_understanding_populated(self, mock_settings_with_key):
        """query_understanding should contain the planner's output."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(tool="hybrid_search", search_query="expanded", dataset="MMLU"),
                    _eval_json(score=9, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("my query", limit=10)

        qu = result.query_understanding
        assert qu["tool"] == "hybrid_search"
        assert qu["search_query"] == "expanded"
        assert qu["dataset"] == "MMLU"

    def test_final_evaluation_string_set(self, mock_settings_with_key):
        """final_evaluation should be a non-empty string after search."""
        results = [_make_result(1)]

        with (
            patch("agents.search_agent.settings", mock_settings_with_key),
            patch("agents.search_agent.hybrid_search", return_value=(results, 1)),
        ):
            from agents.search_agent import SearchAgent

            with patch("agents.search_agent._call_gemini") as mock_llm:
                mock_llm.side_effect = [
                    _plan_json(),
                    _eval_json(score=7, should_continue=False),
                ]

                agent = SearchAgent(db=_make_db(), max_iterations=3)
                result = agent.search("query", limit=10)

        assert result.final_evaluation
        assert isinstance(result.final_evaluation, str)


# ---------------------------------------------------------------------------
# Pipeline strategy (backward compatibility) via API endpoint
# ---------------------------------------------------------------------------


class TestPipelineStrategyBackwardCompat:
    """Tests that the old pipeline strategy still works via the API."""

    def test_pipeline_strategy_calls_intelligent_search(self, test_client):
        """strategy='pipeline' should call the old intelligent_search function."""
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
                "/search/intelligent",
                json={"query": "q", "strategy": "pipeline"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["strategy_used"] == "pipeline"
        assert data["total"] == 1

    def test_agent_strategy_returns_iterations(self, test_client):
        """strategy='agent' response should include iterations list."""
        results = [_make_result(1)]
        from agents.search_agent import AgentSearchResult, SearchIteration

        mock_agent_result = AgentSearchResult(
            results=results,
            total=1,
            iterations=[
                SearchIteration(
                    tool_used="hybrid_search",
                    query="expanded query",
                    filters={"dataset": None, "subject": None},
                    result_count=1,
                    evaluation="score=8/10 — good results",
                )
            ],
            final_evaluation="score=8/10 — good results",
            query_understanding={"tool": "hybrid_search", "search_query": "expanded query"},
        )

        with patch("agents.search_agent.SearchAgent.search", return_value=mock_agent_result):
            response = test_client.post(
                "/search/intelligent",
                json={"query": "test query", "strategy": "agent", "max_iterations": 2},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["strategy_used"] == "agent"
        assert len(data["iterations"]) == 1
        assert data["iterations"][0]["tool_used"] == "hybrid_search"
        assert "final_evaluation" in data
        assert "query_understanding" in data

    def test_default_strategy_is_agent(self, test_client):
        """When no strategy is specified, agent strategy should be used."""
        results = [_make_result(1)]
        from agents.search_agent import AgentSearchResult, SearchIteration

        mock_agent_result = AgentSearchResult(
            results=results,
            total=1,
            iterations=[
                SearchIteration(
                    tool_used="hybrid_search",
                    query="q",
                    filters={},
                    result_count=1,
                    evaluation="score=8/10 — ok",
                )
            ],
            final_evaluation="score=8/10 — ok",
            query_understanding={},
        )

        with patch("agents.search_agent.SearchAgent.search", return_value=mock_agent_result):
            response = test_client.post("/search/intelligent", json={"query": "q"})

        assert response.status_code == 200
        data = response.json()
        assert data["strategy_used"] == "agent"

    def test_max_iterations_validation(self, test_client):
        """max_iterations outside 1-5 should be rejected with 422."""
        response = test_client.post(
            "/search/intelligent",
            json={"query": "test", "max_iterations": 0},
        )
        assert response.status_code == 422

        response = test_client.post(
            "/search/intelligent",
            json={"query": "test", "max_iterations": 6},
        )
        assert response.status_code == 422

    def test_backward_compat_no_strategy_field(self, test_client):
        """Old clients that don't send strategy should still get a valid response."""
        results = [_make_result(1)]
        from agents.search_agent import AgentSearchResult

        mock_agent_result = AgentSearchResult(
            results=results,
            total=1,
            iterations=[],
            final_evaluation="",
            query_understanding={},
        )

        with patch("agents.search_agent.SearchAgent.search", return_value=mock_agent_result):
            response = test_client.post("/search/intelligent", json={"query": "q", "limit": 5})

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert "results" in data
        assert "total" in data
        assert "metadata" in data


# ---------------------------------------------------------------------------
# SearchIteration dataclass
# ---------------------------------------------------------------------------


class TestSearchIterationDataclass:
    """Tests for the SearchIteration dataclass."""

    def test_evaluation_defaults_to_none(self):
        """evaluation field should default to None."""
        from agents.search_agent import SearchIteration

        it = SearchIteration(
            tool_used="keyword_search",
            query="q",
            filters={},
            result_count=5,
        )
        assert it.evaluation is None

    def test_all_fields_accessible(self):
        """All fields should be set and accessible."""
        from agents.search_agent import SearchIteration

        it = SearchIteration(
            tool_used="semantic_search",
            query="test",
            filters={"dataset": "MMLU"},
            result_count=10,
            evaluation="score=7/10 — decent",
        )
        assert it.tool_used == "semantic_search"
        assert it.query == "test"
        assert it.filters == {"dataset": "MMLU"}
        assert it.result_count == 10
        assert it.evaluation == "score=7/10 — decent"


# ---------------------------------------------------------------------------
# AgentSearchResult dataclass
# ---------------------------------------------------------------------------


class TestAgentSearchResultDataclass:
    """Tests for the AgentSearchResult dataclass."""

    def test_all_fields_accessible(self):
        """All fields should be set and accessible."""
        from agents.search_agent import AgentSearchResult, SearchIteration

        result = AgentSearchResult(
            results=[_make_result(1)],
            total=1,
            iterations=[
                SearchIteration(
                    tool_used="hybrid_search",
                    query="q",
                    filters={},
                    result_count=1,
                )
            ],
            final_evaluation="score=9/10",
            query_understanding={"tool": "hybrid_search"},
        )
        assert result.total == 1
        assert len(result.results) == 1
        assert len(result.iterations) == 1
        assert result.final_evaluation == "score=9/10"
        assert result.query_understanding == {"tool": "hybrid_search"}
