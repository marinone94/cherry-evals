"""LLM-powered query understanding agent.

Parses natural language queries into structured search parameters using
Google Gemini Flash for speed.
"""

import json
import logging

from google import genai

from agents.prompts.search import QUERY_UNDERSTANDING_PROMPT
from cherry_evals.config import settings
from core.safety.content_wrapper import wrap_external_content

logger = logging.getLogger(__name__)

# Datasets available in Cherry Evals
AVAILABLE_DATASETS = ["MMLU", "HumanEval", "GSM8K", "HellaSwag", "TruthfulQA", "ARC"]

# Task types available in Cherry Evals
AVAILABLE_TASK_TYPES = [
    "multiple_choice",
    "code_generation",
    "math_reasoning",
    "commonsense_reasoning",
    "truthfulness",
    "science_qa",
]

_GEMINI_MODEL = "gemini-2.0-flash"


def _build_parse_prompt(query: str, available_datasets: list[str] | None) -> str:
    """Build the full prompt for query parsing."""
    datasets = available_datasets or AVAILABLE_DATASETS
    safe_query = wrap_external_content(query, source="user_query")
    user_message = f"Available datasets: {', '.join(datasets)}\n\nQuery:\n{safe_query}"
    return f"{QUERY_UNDERSTANDING_PROMPT}\n\n{user_message}"


def _parse_llm_response(response_text: str, original_query: str) -> dict:
    """Parse and validate the LLM JSON response.

    Falls back to a safe default dict on any parse error.
    """
    try:
        # Strip markdown code fences if present
        text = response_text.strip()
        if text.startswith("```"):
            # Remove opening fence (```json or ```)
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            # Remove closing fence
            if "```" in text:
                text = text[: text.rfind("```")]
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse query agent JSON response: %s", exc)
        return _default_result(original_query)

    # Validate required fields exist; fill defaults for missing optional ones
    if not isinstance(parsed, dict) or "search_query" not in parsed:
        logger.warning("Query agent response missing required fields")
        return _default_result(original_query)

    return {
        "search_query": parsed.get("search_query") or original_query,
        "dataset": parsed.get("dataset"),
        "subject": parsed.get("subject"),
        "task_type": parsed.get("task_type"),
        "explanation": parsed.get("explanation", ""),
    }


def _default_result(query: str) -> dict:
    """Return a safe fallback result that passes through the original query."""
    return {
        "search_query": query,
        "dataset": None,
        "subject": None,
        "task_type": None,
        "explanation": "Fallback: LLM call failed or returned invalid response.",
    }


def parse_query(query: str, available_datasets: list[str] | None = None) -> dict:
    """Parse a natural language query into structured search parameters.

    Calls Gemini Flash to understand the intent behind the query and extract:
    - An optimized/expanded search query string
    - An optional dataset filter (e.g., "MMLU", "GSM8K")
    - An optional subject filter (for MMLU subjects like "biology")
    - An optional task type filter
    - A brief explanation of the parsing decision

    On any failure (network error, invalid API key, JSON parse error), returns
    the original query with all filters set to None so search still works.

    Args:
        query: The raw natural language query from the user.
        available_datasets: Optional list of dataset names to pass to the model.
                            Defaults to the full list of available datasets.

    Returns:
        Dict with keys: search_query, dataset, subject, task_type, explanation.
    """
    if not settings.google_api_key:
        logger.warning("GOOGLE_API_KEY not set — skipping query understanding")
        return _default_result(query)

    try:
        client = genai.Client(api_key=settings.google_api_key)
        prompt = _build_parse_prompt(query, available_datasets)
        response = client.models.generate_content(model=_GEMINI_MODEL, contents=prompt)
        return _parse_llm_response(response.text, query)
    except Exception as exc:
        logger.warning("Query agent LLM call failed: %s", exc)
        return _default_result(query)
