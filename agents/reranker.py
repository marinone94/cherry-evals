"""LLM-powered search result re-ranker.

Re-ranks search results by relevance and diversity using Google Gemini Flash.
"""

import json
import logging

from google import genai

from agents.prompts.search import RERANKING_PROMPT
from cherry_evals.config import settings

logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-2.0-flash"

# Limit input to the model to avoid context overflow
_MAX_INPUT_RESULTS = 50
# Max characters of question/answer to include per result
_SNIPPET_LENGTH = 120


def _build_rerank_prompt(query: str, results: list[dict]) -> str:
    """Build the prompt for re-ranking, truncating result text to keep it concise."""
    summaries = []
    for r in results[:_MAX_INPUT_RESULTS]:
        question_snippet = (r.get("question") or "")[:_SNIPPET_LENGTH]
        answer_snippet = (r.get("answer") or "")[:_SNIPPET_LENGTH]
        metadata = r.get("example_metadata") or {}
        summaries.append(
            {
                "id": r["id"],
                "question": question_snippet,
                "answer": answer_snippet,
                "dataset": r.get("dataset_name", ""),
                "subject": metadata.get("subject", ""),
            }
        )

    user_message = f"Query: {query}\n\nResults to rank:\n{json.dumps(summaries, indent=2)}"
    return f"{RERANKING_PROMPT}\n\n{user_message}"


def _apply_ranking(ranked_ids: list[int], results: list[dict]) -> list[dict]:
    """Apply a ranked ID list to reorder results.

    IDs in ranked_ids that are not present in results are ignored.
    Results not present in ranked_ids are appended at the end.
    """
    result_map = {r["id"]: r for r in results}
    reordered = []
    seen = set()

    for rid in ranked_ids:
        if rid in result_map and rid not in seen:
            reordered.append(result_map[rid])
            seen.add(rid)

    # Append any results that the LLM missed (preserve original order)
    for r in results:
        if r["id"] not in seen:
            reordered.append(r)

    return reordered


def rerank_results(
    query: str,
    results: list[dict],
    limit: int = 20,
) -> list[dict]:
    """Re-rank search results by relevance and diversity using Gemini Flash.

    Sends the top _MAX_INPUT_RESULTS results to the model and asks it to
    re-order them. The re-ranked list is then truncated to `limit`.

    On any LLM failure (network error, bad JSON, etc.) the original result
    order is returned unchanged so search still works.

    Args:
        query: The original or parsed search query.
        results: List of result dicts from hybrid / keyword search.
        limit: Maximum number of results to return after re-ranking.

    Returns:
        Re-ordered list of result dicts, at most `limit` items.
    """
    if not results:
        return results

    if not settings.google_api_key:
        logger.warning("GOOGLE_API_KEY not set — skipping re-ranking")
        return results[:limit]

    try:
        client = genai.Client(api_key=settings.google_api_key)
        prompt = _build_rerank_prompt(query, results)
        response = client.models.generate_content(model=_GEMINI_MODEL, contents=prompt)
        ranked_ids, explanation = _parse_rerank_response(response.text)
        reordered = _apply_ranking(ranked_ids, results)
        logger.debug("Re-ranking explanation: %s", explanation)
        return reordered[:limit]
    except Exception as exc:
        logger.warning("Re-ranker LLM call failed: %s", exc)
        return results[:limit]


def _parse_rerank_response(response_text: str) -> tuple[list[int], str]:
    """Parse the LLM re-ranking response.

    Returns (ranked_ids, explanation). On parse failure returns ([], "").
    """
    try:
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if "```" in text:
                text = text[: text.rfind("```")]
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse re-ranker JSON response: %s", exc)
        return [], ""

    if not isinstance(parsed, dict) or "ranked_ids" not in parsed:
        logger.warning("Re-ranker response missing ranked_ids field")
        return [], ""

    ranked_ids = parsed.get("ranked_ids", [])
    explanation = parsed.get("explanation", "")

    # Ensure ranked_ids contains integers
    try:
        ranked_ids = [int(rid) for rid in ranked_ids]
    except (TypeError, ValueError):
        logger.warning("Re-ranker ranked_ids contains non-integer values")
        return [], ""

    return ranked_ids, explanation
