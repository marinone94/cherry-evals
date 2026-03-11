"""Agentic export — generates custom export formats on-the-fly.

Instead of being limited to pre-built formats (JSON, JSONL, CSV, Langfuse),
this agent can export collections to ANY format the user describes:
1. User describes the target format (or names a platform like "Inspect AI")
2. LLM generates a convert function that maps examples to the target schema
3. The function is validated against sample data
4. The full collection is converted and returned

Known formats still use the fast pre-built converters. The agent only activates
for custom/unknown formats.

Uses Gemini Flash for all LLM calls. Graceful degradation throughout.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from agents.prompts.export import (
    ELEUTHER_HARNESS_HINT,
    FORMAT_GENERATOR_PROMPT,
    INSPECT_AI_HINT,
    LANGSMITH_HINT,
)
from cherry_evals.config import settings
from core.safety.content_wrapper import wrap_external_content
from core.safety.output_scanner import sanitize_error_message

logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-2.0-flash"

# Known format hints — appended to prompt when user mentions these platforms
_FORMAT_HINTS: dict[str, str] = {
    "inspect": INSPECT_AI_HINT,
    "inspect_ai": INSPECT_AI_HINT,
    "inspect ai": INSPECT_AI_HINT,
    "langsmith": LANGSMITH_HINT,
    "eleuther": ELEUTHER_HARNESS_HINT,
    "lm-eval": ELEUTHER_HARNESS_HINT,
    "lm_eval": ELEUTHER_HARNESS_HINT,
    "harness": ELEUTHER_HARNESS_HINT,
}

# Pre-built formats that don't need the agent
BUILTIN_FORMATS = {"json", "jsonl", "csv", "langfuse"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ExportPlan:
    """Plan for a custom export."""

    format_description: str
    convert_function_code: str
    file_extension: str
    content_type: str
    explanation: str


@dataclass
class ExportResult:
    """Result from agentic export."""

    success: bool
    content: str
    file_extension: str
    content_type: str
    plan: ExportPlan | None
    num_examples: int
    errors: list[str] = field(default_factory=list)


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


def _compile_convert_function(code: str) -> callable | None:
    """Safely compile a convert function from LLM-generated code.

    Only allows json, csv, io from stdlib. Builtins are restricted to a safe
    allowlist — no open(), exec(), eval(), __import__(), etc.
    """
    import csv
    import io
    import re

    safe_builtins = {
        "True": True,
        "False": False,
        "None": None,
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "float": float,
        "frozenset": frozenset,
        "int": int,
        "isinstance": isinstance,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,
    }

    try:
        safe_globals = {
            "__builtins__": safe_builtins,
            "json": json,
            "csv": csv,
            "io": io,
            "re": re,
        }
        namespace: dict = {}
        exec(code, safe_globals, namespace)  # noqa: S102
        fn = namespace.get("convert")
        if fn is None or not callable(fn):
            logger.warning("Generated code does not define a callable 'convert'")
            return None
        return fn
    except Exception as exc:
        logger.warning("Failed to compile convert function: %s", exc)
        return None


def _validate_convert_function(fn: callable, sample_examples: list[dict]) -> list[str]:
    """Run the convert function against sample data and return any errors."""
    errors: list[str] = []
    try:
        result = fn(sample_examples)
        if not isinstance(result, str):
            errors.append(f"convert returned {type(result).__name__}, expected str")
        elif not result.strip():
            errors.append("convert returned empty string")
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return errors


def _examples_to_dicts(examples) -> list[dict]:
    """Convert Example ORM objects to plain dicts for the agent."""
    result = []
    for ex in examples:
        d = {
            "id": ex.id,
            "dataset_id": ex.dataset_id,
            "question": ex.question,
            "answer": ex.answer,
            "choices": ex.choices,
        }
        if hasattr(ex, "dataset") and ex.dataset:
            d["dataset_name"] = ex.dataset.name
        if ex.example_metadata:
            d["metadata"] = ex.example_metadata
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# ExportAgent
# ---------------------------------------------------------------------------


class ExportAgent:
    """Autonomous agent that exports collections to any format.

    For builtin formats (json, jsonl, csv, langfuse), delegates to pre-built
    converters. For custom formats, uses an LLM to generate a converter function.

    Workflow for custom formats:
      1. Parse format description, detect known platform hints
      2. LLM generates a convert(examples) -> str function
      3. Validate against sample data
      4. Run on full collection
    """

    def generate_converter(self, format_description: str) -> ExportPlan | None:
        """Use LLM to generate a custom converter function.

        Args:
            format_description: Natural language description of the target format.
                Can be a platform name ("Inspect AI") or a detailed spec.

        Returns:
            ExportPlan with the generated code, or None on failure.
        """
        # Detect known platform hints
        hint = ""
        desc_lower = format_description.lower()
        for keyword, platform_hint in _FORMAT_HINTS.items():
            if keyword in desc_lower:
                hint = f"\n\nPlatform format reference:\n{platform_hint}"
                break

        safe_desc = wrap_external_content(format_description, source="format_description")
        prompt = f"{FORMAT_GENERATOR_PROMPT}{hint}\n\nTarget format description:\n{safe_desc}"

        response_text = _call_gemini(prompt)
        if not response_text:
            return None

        try:
            parsed = json.loads(_strip_fences(response_text))
            if not isinstance(parsed, dict) or "convert_function" not in parsed:
                logger.warning("Format generator response missing convert_function")
                return None

            return ExportPlan(
                format_description=format_description,
                convert_function_code=parsed["convert_function"],
                file_extension=parsed.get("file_extension", ".txt"),
                content_type=parsed.get("content_type", "text/plain"),
                explanation=parsed.get("explanation", ""),
            )
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse format generator response: %s", exc)
            return None

    def export(
        self,
        examples,
        format_description: str,
        dataset_names: dict[int, str] | None = None,
    ) -> ExportResult:
        """Export examples to a custom format.

        Args:
            examples: List of Example ORM objects or dicts.
            format_description: Natural language description of the target format.
            dataset_names: Optional mapping of dataset_id -> name.

        Returns:
            ExportResult with the converted content or errors.
        """
        # Check if this is a builtin format
        fmt_lower = format_description.lower().strip()
        if fmt_lower in BUILTIN_FORMATS:
            return self._export_builtin(examples, fmt_lower, dataset_names)

        # Convert ORM objects to dicts if needed
        if examples and hasattr(examples[0], "question"):
            example_dicts = _examples_to_dicts(examples)
        else:
            example_dicts = list(examples)

        # Inject dataset names
        if dataset_names:
            for d in example_dicts:
                if "dataset_name" not in d and d.get("dataset_id") in dataset_names:
                    d["dataset_name"] = dataset_names[d["dataset_id"]]

        # Step 1: Generate converter
        plan = self.generate_converter(format_description)
        if not plan:
            return ExportResult(
                success=False,
                content="",
                file_extension=".txt",
                content_type="text/plain",
                plan=None,
                num_examples=len(example_dicts),
                errors=["LLM failed to generate a converter for this format."],
            )

        # Step 2: Compile
        convert_fn = _compile_convert_function(plan.convert_function_code)
        if convert_fn is None:
            return ExportResult(
                success=False,
                content="",
                file_extension=plan.file_extension,
                content_type=plan.content_type,
                plan=plan,
                num_examples=len(example_dicts),
                errors=["Generated convert function failed to compile."],
            )

        # Step 3: Validate against sample
        sample = example_dicts[:3] if example_dicts else []
        validation_errors = _validate_convert_function(convert_fn, sample)
        if validation_errors:
            return ExportResult(
                success=False,
                content="",
                file_extension=plan.file_extension,
                content_type=plan.content_type,
                plan=plan,
                num_examples=len(example_dicts),
                errors=["Converter validation failed:"] + validation_errors,
            )

        # Step 4: Run on full data
        try:
            content = convert_fn(example_dicts)
        except Exception as exc:
            logger.error("Export conversion failed: %s", exc)
            return ExportResult(
                success=False,
                content="",
                file_extension=plan.file_extension,
                content_type=plan.content_type,
                plan=plan,
                num_examples=len(example_dicts),
                errors=[f"Conversion failed: {sanitize_error_message(exc)}"],
            )

        return ExportResult(
            success=True,
            content=content,
            file_extension=plan.file_extension,
            content_type=plan.content_type,
            plan=plan,
            num_examples=len(example_dicts),
        )

    def _export_builtin(
        self,
        examples,
        fmt: str,
        dataset_names: dict[int, str] | None = None,
    ) -> ExportResult:
        """Delegate to pre-built exporters for known formats."""
        from core.export.formats import to_csv, to_json, to_jsonl

        ext_map = {"json": ".json", "jsonl": ".jsonl", "csv": ".csv", "langfuse": ".json"}
        ct_map = {
            "json": "application/json",
            "jsonl": "application/x-ndjson",
            "csv": "text/csv",
            "langfuse": "application/json",
        }

        try:
            if fmt == "json":
                content = to_json(examples, dataset_names)
            elif fmt == "jsonl":
                content = to_jsonl(examples, dataset_names)
            elif fmt == "csv":
                content = to_csv(examples, dataset_names)
            elif fmt == "langfuse":
                from core.export.langfuse_export import export_to_langfuse

                result = export_to_langfuse(examples, "collection", "", dataset_names)
                content = json.dumps(result, indent=2)
            else:
                return ExportResult(
                    success=False,
                    content="",
                    file_extension=".txt",
                    content_type="text/plain",
                    plan=None,
                    num_examples=len(examples) if examples else 0,
                    errors=[f"Unknown builtin format: {fmt}"],
                )

            return ExportResult(
                success=True,
                content=content,
                file_extension=ext_map.get(fmt, ".txt"),
                content_type=ct_map.get(fmt, "text/plain"),
                plan=None,
                num_examples=len(examples) if examples else 0,
            )
        except Exception as exc:
            return ExportResult(
                success=False,
                content="",
                file_extension=ext_map.get(fmt, ".txt"),
                content_type=ct_map.get(fmt, "text/plain"),
                plan=None,
                num_examples=len(examples) if examples else 0,
                errors=[f"Builtin export failed: {sanitize_error_message(exc)}"],
            )
