"""Agentic ingestion — discovers and ingests arbitrary HuggingFace datasets.

Instead of requiring a pre-built adapter for each dataset, this agent:
1. Discovers datasets matching a user's description (or takes a direct HF ID)
2. Inspects the dataset schema (column names, types, sample rows)
3. Generates a parse_row function on-the-fly using an LLM
4. Validates the generated code against sample rows
5. Runs the full ingestion using the standard pipeline

The generated adapter code can optionally be saved to the codebase for reuse.

Uses Gemini Flash for all LLM calls. Graceful degradation throughout.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from agents.prompts.ingestion import DATASET_DISCOVERY_PROMPT, SCHEMA_ANALYSIS_PROMPT
from cherry_evals.config import settings

logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-2.0-flash"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class IngestionPlan:
    """Plan for ingesting a discovered dataset."""

    hf_dataset_id: str
    hf_config: str | None
    name: str
    description: str
    task_type: str
    license: str
    source: str
    splits: list[str]
    parse_function_code: str
    explanation: str
    question_field: str
    answer_field: str


@dataclass
class IngestionResult:
    """Result from agentic ingestion."""

    success: bool
    dataset_name: str
    total_examples: int
    splits: dict[str, int]
    plan: IngestionPlan | None
    errors: list[str] = field(default_factory=list)
    adapter_code: str | None = None  # Full adapter class code for saving


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


def _compile_parse_function(code: str) -> callable | None:
    """Safely compile a parse_row function from LLM-generated code.

    Returns the callable or None if compilation fails.
    """
    try:
        namespace: dict = {}
        exec(code, {"__builtins__": __builtins__}, namespace)  # noqa: S102
        fn = namespace.get("parse_row")
        if fn is None or not callable(fn):
            logger.warning("Generated code does not define a callable 'parse_row'")
            return None
        return fn
    except Exception as exc:
        logger.warning("Failed to compile parse_row: %s", exc)
        return None


def _validate_parse_function(fn: callable, sample_rows: list[dict], dataset_id: int) -> list[str]:
    """Run the parse function against sample rows and return any errors."""
    errors: list[str] = []
    required_keys = {"dataset_id", "question", "split"}

    for i, row in enumerate(sample_rows[:5]):
        try:
            result = fn(row, dataset_id, "validation")
            if not isinstance(result, dict):
                errors.append(f"Row {i}: parse_row returned {type(result).__name__}, expected dict")
                continue
            missing = required_keys - set(result.keys())
            if missing:
                errors.append(f"Row {i}: missing keys {missing}")
            if not result.get("question"):
                errors.append(f"Row {i}: question is empty or None")
        except Exception as exc:
            errors.append(f"Row {i}: {type(exc).__name__}: {exc}")

    return errors


def _generate_adapter_class_code(plan: IngestionPlan) -> str:
    """Generate a full DatasetAdapter subclass from the plan, for saving to codebase."""
    safe_name = plan.name.replace(" ", "").replace("-", "")
    return f'''"""Auto-generated adapter for {plan.name}."""

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example


class {safe_name}Adapter(DatasetAdapter):
    """Adapter for {plan.name} dataset."""

    @property
    def name(self) -> str:
        return "{plan.name}"

    @property
    def source(self) -> str:
        return "{plan.source}"

    @property
    def hf_dataset_id(self) -> str:
        return "{plan.hf_dataset_id}"

    @property
    def hf_config(self) -> str | None:
        return {repr(plan.hf_config)}

    @property
    def license(self) -> str:
        return "{plan.license}"

    @property
    def task_type(self) -> str:
        return "{plan.task_type}"

    @property
    def description(self) -> str:
        return """{plan.description}"""

    @property
    def splits(self) -> list[str]:
        return {plan.splits!r}

    def parse_example(self, row: dict, dataset_id: int, split: str) -> Example:
        parsed = _parse_row(row, dataset_id, split)
        return Example(**parsed)


{plan.parse_function_code}


def _parse_row(row: dict, dataset_id: int, split: str) -> dict:
    return parse_row(row, dataset_id, split)
'''


# ---------------------------------------------------------------------------
# IngestionAgent
# ---------------------------------------------------------------------------


class IngestionAgent:
    """Autonomous agent that discovers and ingests arbitrary HuggingFace datasets.

    Workflow:
      1. Discover: find a dataset matching the user's description (or accept a direct HF ID)
      2. Inspect: load dataset metadata and sample rows
      3. Generate: LLM writes a parse_row function for the dataset's schema
      4. Validate: test parse_row against sample rows
      5. Ingest: run the standard ingestion pipeline with the generated function
      6. Optionally: generate a full adapter class for permanent inclusion

    All LLM calls use Gemini Flash. Any failure degrades gracefully with
    descriptive error messages.
    """

    def __init__(self, max_examples: int | None = None, batch_size: int = 1000) -> None:
        self.max_examples = max_examples
        self.batch_size = batch_size

    def discover_dataset(self, description: str) -> dict | None:
        """Use LLM to find a HuggingFace dataset matching the description.

        Args:
            description: Natural language description of what dataset to find.
                Can also be a direct HuggingFace dataset ID (e.g., "openai/gsm8k").

        Returns:
            Dict with dataset metadata, or None if discovery fails.
        """
        # If it looks like a direct HF ID, skip discovery
        if "/" in description and len(description.split()) <= 2:
            return {
                "hf_dataset_id": description.strip(),
                "hf_config": None,
                "name": description.split("/")[-1],
                "description": f"Dataset from {description}",
                "task_type": "open_ended",
                "license": "unknown",
                "source": f"HuggingFace:{description.strip()}",
                "splits": ["train", "validation", "test"],
                "rationale": "Direct HuggingFace ID provided.",
            }

        prompt = f"{DATASET_DISCOVERY_PROMPT}\n\nUser request: {description}"
        response_text = _call_gemini(prompt)
        if not response_text:
            return None

        try:
            parsed = json.loads(_strip_fences(response_text))
            if not isinstance(parsed, dict) or "hf_dataset_id" not in parsed:
                logger.warning("Discovery response missing hf_dataset_id")
                return None
            return parsed
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse discovery response: %s", exc)
            return None

    def inspect_schema(self, hf_dataset_id: str, hf_config: str | None = None) -> dict | None:
        """Load a dataset from HuggingFace and inspect its schema.

        Returns dict with column_info, sample_rows, and available_splits.
        """
        try:
            from datasets import load_dataset

            if hf_config:
                ds = load_dataset(hf_dataset_id, hf_config, streaming=True)
            else:
                ds = load_dataset(hf_dataset_id, streaming=True)

            # Get available splits
            available_splits = list(ds.keys()) if hasattr(ds, "keys") else []

            # Get sample rows from first available split
            sample_split = available_splits[0] if available_splits else "train"
            sample_rows = []
            try:
                for i, row in enumerate(ds[sample_split]):
                    sample_rows.append(dict(row))
                    if i >= 4:
                        break
            except Exception as exc:
                logger.warning("Failed to get sample rows: %s", exc)

            # Extract column info
            column_info = {}
            if sample_rows:
                for key, value in sample_rows[0].items():
                    column_info[key] = type(value).__name__

            return {
                "hf_dataset_id": hf_dataset_id,
                "hf_config": hf_config,
                "available_splits": available_splits,
                "column_info": column_info,
                "sample_rows": sample_rows,
            }
        except Exception as exc:
            logger.warning("Failed to inspect dataset %s: %s", hf_dataset_id, exc)
            return None

    def generate_parse_function(self, schema_info: dict) -> dict | None:
        """Use LLM to generate a parse_row function for the dataset's schema.

        Args:
            schema_info: Output from inspect_schema().

        Returns:
            Dict with parse_function code and metadata, or None on failure.
        """
        user_msg = (
            f"Dataset: {schema_info['hf_dataset_id']}\n"
            f"Columns: {json.dumps(schema_info['column_info'], indent=2)}\n"
            f"Sample rows:\n{json.dumps(schema_info['sample_rows'][:3], indent=2, default=str)}"
        )
        prompt = f"{SCHEMA_ANALYSIS_PROMPT}\n\n{user_msg}"

        response_text = _call_gemini(prompt)
        if not response_text:
            return None

        try:
            parsed = json.loads(_strip_fences(response_text))
            if not isinstance(parsed, dict) or "parse_function" not in parsed:
                logger.warning("Schema analysis response missing parse_function")
                return None
            return parsed
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse schema analysis response: %s", exc)
            return None

    def ingest(
        self,
        description: str,
        hf_dataset_id: str | None = None,
        hf_config: str | None = None,
    ) -> IngestionResult:
        """Full agentic ingestion pipeline.

        Args:
            description: What kind of dataset to ingest (or the HF ID).
            hf_dataset_id: Optional direct HuggingFace dataset ID (skips discovery).
            hf_config: Optional HuggingFace config/subset name.

        Returns:
            IngestionResult with success status, stats, and optionally the adapter code.
        """
        # Step 1: Discover
        if hf_dataset_id:
            discovery = {
                "hf_dataset_id": hf_dataset_id,
                "hf_config": hf_config,
                "name": hf_dataset_id.split("/")[-1] if "/" in hf_dataset_id else hf_dataset_id,
                "description": description,
                "task_type": "open_ended",
                "license": "unknown",
                "source": f"HuggingFace:{hf_dataset_id}",
                "splits": ["train", "validation", "test"],
            }
        else:
            discovery = self.discover_dataset(description)
            if not discovery:
                return IngestionResult(
                    success=False,
                    dataset_name="unknown",
                    total_examples=0,
                    splits={},
                    plan=None,
                    errors=["Failed to discover a matching dataset."],
                )

        logger.info("Discovered dataset: %s (%s)", discovery["name"], discovery["hf_dataset_id"])

        # Step 2: Inspect schema
        schema_info = self.inspect_schema(
            discovery["hf_dataset_id"],
            discovery.get("hf_config"),
        )
        if not schema_info:
            return IngestionResult(
                success=False,
                dataset_name=discovery.get("name", "unknown"),
                total_examples=0,
                splits={},
                plan=None,
                errors=[f"Failed to inspect schema for {discovery['hf_dataset_id']}."],
            )

        # Use actual available splits
        available_splits = schema_info.get("available_splits", [])
        splits = [s for s in discovery.get("splits", []) if s in available_splits]
        if not splits:
            splits = available_splits[:3]  # Take first 3 available

        # Step 3: Generate parse function
        parse_result = self.generate_parse_function(schema_info)
        if not parse_result:
            return IngestionResult(
                success=False,
                dataset_name=discovery.get("name", "unknown"),
                total_examples=0,
                splits={},
                plan=None,
                errors=["LLM failed to generate a parse function for this schema."],
            )

        parse_code = parse_result["parse_function"]

        # Step 4: Compile and validate
        parse_fn = _compile_parse_function(parse_code)
        if parse_fn is None:
            return IngestionResult(
                success=False,
                dataset_name=discovery.get("name", "unknown"),
                total_examples=0,
                splits={},
                plan=None,
                errors=["Generated parse function failed to compile."],
            )

        validation_errors = _validate_parse_function(
            parse_fn,
            schema_info.get("sample_rows", []),
            dataset_id=0,
        )
        if validation_errors:
            return IngestionResult(
                success=False,
                dataset_name=discovery.get("name", "unknown"),
                total_examples=0,
                splits={},
                plan=None,
                errors=["Parse function validation failed:"] + validation_errors,
            )

        # Build plan
        plan = IngestionPlan(
            hf_dataset_id=discovery["hf_dataset_id"],
            hf_config=discovery.get("hf_config"),
            name=discovery["name"],
            description=discovery.get("description", ""),
            task_type=parse_result.get("task_type", discovery.get("task_type", "open_ended")),
            license=discovery.get("license", "unknown"),
            source=discovery.get("source", f"HuggingFace:{discovery['hf_dataset_id']}"),
            splits=splits,
            parse_function_code=parse_code,
            explanation=parse_result.get("explanation", ""),
            question_field=parse_result.get("question_field", ""),
            answer_field=parse_result.get("answer_field", ""),
        )

        # Step 5: Run ingestion
        try:
            stats = self._run_ingestion(plan, parse_fn)
        except Exception as exc:
            logger.error("Ingestion failed: %s", exc)
            return IngestionResult(
                success=False,
                dataset_name=plan.name,
                total_examples=0,
                splits={},
                plan=plan,
                errors=[f"Ingestion execution failed: {exc}"],
            )

        # Generate adapter class code for optional saving
        adapter_code = _generate_adapter_class_code(plan)

        return IngestionResult(
            success=True,
            dataset_name=plan.name,
            total_examples=stats.get("total_examples", 0),
            splits=stats.get("splits", {}),
            plan=plan,
            adapter_code=adapter_code,
        )

    def _run_ingestion(self, plan: IngestionPlan, parse_fn: callable) -> dict:
        """Execute the actual ingestion using the generated parse function."""
        from datasets import load_dataset
        from sqlalchemy import select

        from db.postgres.base import SessionLocal
        from db.postgres.models import Dataset, Example

        if plan.hf_config:
            hf_dataset = load_dataset(plan.hf_dataset_id, plan.hf_config)
        else:
            hf_dataset = load_dataset(plan.hf_dataset_id)

        db = SessionLocal()
        try:
            # Get or create dataset record
            stmt = select(Dataset).where(Dataset.name == plan.name)
            dataset = db.execute(stmt).scalar_one_or_none()

            if dataset is None:
                dataset = Dataset(
                    name=plan.name,
                    source=plan.source,
                    license=plan.license,
                    task_type=plan.task_type,
                    description=plan.description,
                    stats={},
                )
                db.add(dataset)
                db.commit()
                db.refresh(dataset)
            else:
                # Idempotent: clear old examples
                db.query(Example).filter(Example.dataset_id == dataset.id).delete()
                db.commit()

            total = 0
            splits_count: dict[str, int] = {}

            for split_name in plan.splits:
                if split_name not in hf_dataset:
                    continue

                split_data = hf_dataset[split_name]
                batch: list[Example] = []
                num = len(split_data)
                if self.max_examples is not None:
                    remaining = self.max_examples - total
                    if remaining <= 0:
                        break
                    num = min(num, remaining)

                for i in range(num):
                    row = split_data[i]
                    parsed = parse_fn(row, dataset.id, split_name)
                    example = Example(
                        dataset_id=parsed["dataset_id"],
                        question=parsed["question"],
                        answer=parsed.get("answer"),
                        choices=parsed.get("choices"),
                        example_metadata=parsed.get("example_metadata"),
                        split=parsed.get("split", split_name),
                    )
                    batch.append(example)

                    if len(batch) >= self.batch_size:
                        db.bulk_save_objects(batch)
                        db.commit()
                        batch = []

                    total += 1

                if batch:
                    db.bulk_save_objects(batch)
                    db.commit()

                splits_count[split_name] = num

            dataset.stats = {"total_examples": total, "splits": splits_count}
            db.commit()

            return {
                "dataset_id": dataset.id,
                "dataset_name": dataset.name,
                "total_examples": total,
                "splits": splits_count,
            }
        finally:
            db.close()
