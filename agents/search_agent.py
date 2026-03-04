"""Autonomous search agent that iterates and refines to find the best results.

Unlike the fixed pipeline (parse → search → rerank), this agent:
1. Plans a search strategy based on the query
2. Executes the chosen tool
3. Evaluates result quality with an LLM
4. Decides whether to refine and try again
5. Combines, deduplicates, and re-ranks across all iterations

The agent uses Gemini Flash for all LLM calls. Each search tool call is
cheap (local DB / Qdrant) — the iteration budget limits LLM calls, not
search calls.

Graceful degradation: any LLM failure causes the agent to proceed with
the results it has rather than erroring out.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from agents.prompts.search import (
    RESULT_EVALUATOR_PROMPT,
    SEARCH_PLANNER_PROMPT,
)
from cherry_evals.config import settings
from core.search.hybrid import hybrid_search
from core.search.keyword import keyword_search
from core.search.semantic import semantic_search

logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-2.0-flash"

# Map canonical dataset names → Qdrant collections
_DATASET_COLLECTION_MAP = {
    "MMLU": "mmlu_embeddings",
    "HumanEval": "humaneval_embeddings",
    "GSM8K": "gsm8k_embeddings",
    "HellaSwag": "hellaswag_embeddings",
    "TruthfulQA": "truthfulqa_embeddings",
    "ARC": "arc_embeddings",
}
_DEFAULT_COLLECTION = "mmlu_embeddings"

_VALID_TOOLS = {"keyword_search", "semantic_search", "hybrid_search"}


@dataclass
class SearchIteration:
    """Record of a single search attempt within the agent loop."""

    tool_used: str
    query: str
    filters: dict
    result_count: int
    evaluation: str | None = None


@dataclass
class AgentSearchResult:
    """Final result from the autonomous search agent."""

    results: list[dict]
    total: int
    iterations: list[SearchIteration]
    final_evaluation: str
    query_understanding: dict


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from LLM JSON output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if "```" in text:
            text = text[: text.rfind("```")]
    return text.strip()


def _call_gemini(prompt: str) -> str | None:
    """Call Gemini Flash and return the response text, or None on failure."""
    if not settings.google_api_key:
        logger.warning("GOOGLE_API_KEY not set — skipping LLM call")
        return None
    try:
        from google import genai

        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(model=_GEMINI_MODEL, contents=prompt)
        return response.text
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc)
        return None


def _resolve_collection(dataset: str | None) -> str:
    if dataset and dataset in _DATASET_COLLECTION_MAP:
        return _DATASET_COLLECTION_MAP[dataset]
    return _DEFAULT_COLLECTION


# ---------------------------------------------------------------------------
# SearchAgent
# ---------------------------------------------------------------------------


class SearchAgent:
    """Autonomous search agent that iterates to find the best results.

    The agent runs a loop:
      1. Plan initial strategy (LLM call 1)
      2. Execute search tool
      3. Evaluate results (LLM call 2..N)
      4. If unsatisfied and iterations remain: refine and repeat from 2
      5. Combine, deduplicate, re-rank, return

    LLM calls are capped at max_iterations (for evaluation steps) plus
    one initial planning call. Graceful degradation throughout.
    """

    def __init__(self, db: Session, max_iterations: int = 3) -> None:
        self.db = db
        self.max_iterations = max(1, min(max_iterations, 5))
        self._history: list[SearchIteration] = []
        self._all_results: list[dict] = []  # Accumulated across iterations
        self._tools: dict = {
            "keyword_search": self._keyword_search,
            "semantic_search": self._semantic_search,
            "hybrid_search": self._hybrid_search,
        }

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 20) -> AgentSearchResult:
        """Run the autonomous search agent loop.

        Args:
            query: Natural language query from the user.
            limit: Maximum number of results to return.

        Returns:
            AgentSearchResult with results, iteration trace, and metadata.
        """
        fetch_limit = min(limit + 30, 200)

        # Step 1: Plan initial strategy
        plan = self._plan_search(query)
        query_understanding = plan

        current_query = plan.get("search_query") or query
        current_tool = plan.get("tool", "hybrid_search")
        if current_tool not in _VALID_TOOLS:
            current_tool = "hybrid_search"
        current_dataset = plan.get("dataset")
        current_subject = plan.get("subject")

        final_evaluation = "No evaluation performed."

        # Step 2: Iterate
        for iteration_num in range(self.max_iterations):
            logger.info(
                "Agent iteration %d/%d: tool=%s query=%r dataset=%r subject=%r",
                iteration_num + 1,
                self.max_iterations,
                current_tool,
                current_query,
                current_dataset,
                current_subject,
            )

            # Execute search tool
            results = self._run_tool(
                tool=current_tool,
                query=current_query,
                dataset=current_dataset,
                subject=current_subject,
                limit=fetch_limit,
            )

            iteration = SearchIteration(
                tool_used=current_tool,
                query=current_query,
                filters={
                    "dataset": current_dataset,
                    "subject": current_subject,
                },
                result_count=len(results),
            )

            # Accumulate results (new results appended; dedup happens later)
            self._all_results.extend(results)

            # Evaluate results quality (LLM call)
            evaluation = self._evaluate_results(
                original_query=query,
                results=results,
            )

            assessment = evaluation.get("assessment", "")
            relevance_score = evaluation.get("relevance_score", 5)
            should_continue = evaluation.get("should_continue", False)
            iteration.evaluation = f"score={relevance_score}/10 — {assessment}"
            final_evaluation = iteration.evaluation

            self._history.append(iteration)

            logger.info(
                "Iteration %d evaluation: score=%s should_continue=%s",
                iteration_num + 1,
                relevance_score,
                should_continue,
            )

            # Stop if satisfied or no more iterations
            if not should_continue or iteration_num >= self.max_iterations - 1:
                break

            # Prepare next iteration from evaluator suggestions
            refined = evaluation.get("refined_query") or current_query
            next_tool = evaluation.get("suggested_tool") or current_tool
            if next_tool not in _VALID_TOOLS:
                next_tool = "hybrid_search"
            next_dataset = evaluation.get("suggested_dataset", current_dataset)
            next_subject = evaluation.get("suggested_subject", current_subject)

            current_query = refined
            current_tool = next_tool
            current_dataset = next_dataset
            current_subject = next_subject

        # Step 3: Deduplicate and rank combined results
        deduplicated = self._deduplicate(self._all_results)
        ranked = self._score_sort(deduplicated)
        paginated = ranked[:limit]

        return AgentSearchResult(
            results=paginated,
            total=len(deduplicated),
            iterations=list(self._history),
            final_evaluation=final_evaluation,
            query_understanding=query_understanding,
        )

    # ------------------------------------------------------------------
    # Search tool wrappers
    # ------------------------------------------------------------------

    def _keyword_search(
        self,
        query: str,
        dataset: str | None,
        subject: str | None,
        limit: int,
    ) -> list[dict]:
        try:
            results, _ = keyword_search(
                db=self.db,
                query=query,
                dataset_name=dataset,
                subject=subject,
                limit=limit,
                offset=0,
            )
            return results
        except Exception as exc:
            logger.warning("keyword_search failed: %s", exc)
            return []

    def _semantic_search(
        self,
        query: str,
        dataset: str | None,
        subject: str | None,
        limit: int,
    ) -> list[dict]:
        collection = _resolve_collection(dataset)
        try:
            return semantic_search(
                query=query,
                collection_name=collection,
                limit=limit,
                subject=subject,
            )
        except Exception as exc:
            logger.warning("semantic_search failed: %s", exc)
            return []

    def _hybrid_search(
        self,
        query: str,
        dataset: str | None,
        subject: str | None,
        limit: int,
    ) -> list[dict]:
        collection = _resolve_collection(dataset)
        try:
            results, _ = hybrid_search(
                db=self.db,
                query=query,
                dataset_name=dataset,
                subject=subject,
                limit=limit,
                offset=0,
                collection_name=collection,
            )
            return results
        except Exception as exc:
            logger.warning("hybrid_search failed, falling back to keyword: %s", exc)
            return self._keyword_search(query, dataset, subject, limit)

    def _run_tool(
        self,
        tool: str,
        query: str,
        dataset: str | None,
        subject: str | None,
        limit: int,
    ) -> list[dict]:
        fn = self._tools.get(tool, self._tools["hybrid_search"])
        return fn(query=query, dataset=dataset, subject=subject, limit=limit)

    # ------------------------------------------------------------------
    # LLM interactions
    # ------------------------------------------------------------------

    def _plan_search(self, query: str) -> dict:
        """Call Gemini to plan the initial search strategy."""
        user_message = f"Query: {query}"
        prompt = f"{SEARCH_PLANNER_PROMPT}\n\n{user_message}"

        response_text = _call_gemini(prompt)
        if not response_text:
            return self._default_plan(query)

        try:
            parsed = json.loads(_strip_fences(response_text))
            if not isinstance(parsed, dict) or "tool" not in parsed:
                return self._default_plan(query)
            return {
                "tool": parsed.get("tool", "hybrid_search"),
                "search_query": parsed.get("search_query") or query,
                "dataset": parsed.get("dataset"),
                "subject": parsed.get("subject"),
                "rationale": parsed.get("rationale", ""),
            }
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse search planner response: %s", exc)
            return self._default_plan(query)

    def _evaluate_results(self, original_query: str, results: list[dict]) -> dict:
        """Call Gemini to evaluate search result quality."""
        snippet_len = 100
        summaries = [
            {
                "id": r["id"],
                "question": (r.get("question") or "")[:snippet_len],
                "dataset": r.get("dataset_name", ""),
                "subject": (r.get("example_metadata") or {}).get("subject", ""),
            }
            for r in results[:40]
        ]

        user_message = f"Query: {original_query}\n\nResults ({len(results)} total):\n" + json.dumps(
            summaries, indent=2
        )
        prompt = f"{RESULT_EVALUATOR_PROMPT}\n\n{user_message}"

        response_text = _call_gemini(prompt)
        if not response_text:
            return self._default_evaluation(results)

        try:
            parsed = json.loads(_strip_fences(response_text))
            if not isinstance(parsed, dict) or "relevance_score" not in parsed:
                return self._default_evaluation(results)
            return parsed
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse result evaluator response: %s", exc)
            return self._default_evaluation(results)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _default_plan(query: str) -> dict:
        return {
            "tool": "hybrid_search",
            "search_query": query,
            "dataset": None,
            "subject": None,
            "rationale": "Fallback: LLM call failed.",
        }

    @staticmethod
    def _default_evaluation(results: list[dict]) -> dict:
        """Conservative evaluation when LLM fails: stop if we have results."""
        has_results = len(results) > 0
        return {
            "relevance_score": 5 if has_results else 0,
            "assessment": "LLM evaluation unavailable.",
            "should_continue": not has_results,
            "refined_query": None,
            "suggested_tool": None,
            "suggested_dataset": None,
            "suggested_subject": None,
        }

    @staticmethod
    def _deduplicate(results: list[dict]) -> list[dict]:
        """Remove duplicate results by example id, keeping the first occurrence."""
        seen: set[int] = set()
        unique: list[dict] = []
        for r in results:
            rid = r.get("id")
            if rid is not None and rid not in seen:
                seen.add(rid)
                unique.append(r)
        return unique

    @staticmethod
    def _score_sort(results: list[dict]) -> list[dict]:
        """Sort by score descending; results without a score go last."""
        return sorted(
            results,
            key=lambda r: (r.get("score") is not None, r.get("score") or 0.0),
            reverse=True,
        )
