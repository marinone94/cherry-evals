"""Unit tests for the ExportAgent.

All LLM calls (via _call_gemini) and pre-built exporter imports are mocked —
no real API, database, or file-system calls.

Test coverage:
  - _strip_fences: code fences removed, no fence passthrough
  - _compile_convert_function: valid code, syntax error, missing function
  - _validate_convert_function: good function, returns non-str, raises, empty string
  - _examples_to_dicts: plain ORM-like objects, with dataset attr, with metadata
  - generate_converter: good LLM response, platform hint detection, missing key,
    LLM failure, malformed JSON
  - export (custom format): full success, LLM failure, compile failure, validation failure,
    convert runtime error
  - export (builtin formats): json, jsonl, csv delegation, builtin failure
  - ExportPlan / ExportResult dataclasses: field defaults
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------


def _sample_convert_code() -> str:
    """Minimal valid convert(examples) -> str function."""
    return (
        "def convert(examples):\n"
        "    import json as _json\n"
        "    return _json.dumps(examples, indent=2)\n"
    )


def _sample_convert_response(
    file_ext: str = ".json",
    content_type: str = "application/json",
) -> str:
    """Valid JSON response from the format-generator LLM call."""
    return json.dumps(
        {
            "convert_function": _sample_convert_code(),
            "file_extension": file_ext,
            "content_type": content_type,
            "explanation": "Outputs examples as a JSON array",
        }
    )


def _make_example_dict(example_id: int = 1, dataset_id: int = 1) -> dict:
    return {
        "id": example_id,
        "dataset_id": dataset_id,
        "question": f"Sample question {example_id}?",
        "answer": f"Answer {example_id}",
        "choices": None,
    }


def _make_orm_example(example_id: int = 1, with_dataset: bool = False, with_metadata: bool = False):
    """Build a mock ORM Example object (has .question attribute)."""
    ex = MagicMock()
    ex.id = example_id
    ex.dataset_id = 1
    ex.question = f"ORM question {example_id}?"
    ex.answer = f"ORM answer {example_id}"
    ex.choices = None
    ex.example_metadata = {"subject": "math"} if with_metadata else None

    if with_dataset:
        ex.dataset = MagicMock()
        ex.dataset.name = "MMLU"
    else:
        ex.dataset = None

    return ex


# ---------------------------------------------------------------------------
# _strip_fences (export_agent version)
# ---------------------------------------------------------------------------


class TestStripFences:
    """Tests for the _strip_fences helper in export_agent."""

    def test_strips_json_fences(self):
        from agents.export_agent import _strip_fences

        fenced = '```json\n{"key": 1}\n```'
        assert _strip_fences(fenced) == '{"key": 1}'

    def test_strips_plain_fences(self):
        from agents.export_agent import _strip_fences

        fenced = "```\nhello\n```"
        assert _strip_fences(fenced) == "hello"

    def test_passthrough_no_fence(self):
        from agents.export_agent import _strip_fences

        raw = '{"convert_function": "def convert(e): return str(e)"}'
        assert _strip_fences(raw) == raw

    def test_strips_surrounding_whitespace(self):
        from agents.export_agent import _strip_fences

        fenced = "  ```\ndata\n```  "
        assert _strip_fences(fenced) == "data"


# ---------------------------------------------------------------------------
# _compile_convert_function
# ---------------------------------------------------------------------------


class TestCompileConvertFunction:
    """Tests for the _compile_convert_function helper."""

    def test_compiles_valid_code(self):
        from agents.export_agent import _compile_convert_function

        fn = _compile_convert_function(_sample_convert_code())
        assert callable(fn)
        result = fn([{"id": 1, "question": "Q?"}])
        assert isinstance(result, str)
        data = json.loads(result)
        assert data[0]["question"] == "Q?"

    def test_returns_none_on_syntax_error(self):
        from agents.export_agent import _compile_convert_function

        fn = _compile_convert_function("def convert(\n  syntax error!!!")
        assert fn is None

    def test_returns_none_when_function_missing(self):
        from agents.export_agent import _compile_convert_function

        code = "x = 42\n"  # No convert defined
        fn = _compile_convert_function(code)
        assert fn is None

    def test_returns_none_on_runtime_error_during_exec(self):
        from agents.export_agent import _compile_convert_function

        code = "raise ValueError('bad code')\n"
        fn = _compile_convert_function(code)
        assert fn is None

    def test_json_module_available_in_compiled_code(self):
        """The compiled sandbox must expose json so code can use json.dumps."""
        from agents.export_agent import _compile_convert_function

        code = "def convert(examples):\n    return json.dumps(examples)\n"
        fn = _compile_convert_function(code)
        assert fn is not None
        result = fn([{"a": 1}])
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# _validate_convert_function
# ---------------------------------------------------------------------------


class TestValidateConvertFunction:
    """Tests for the _validate_convert_function helper."""

    def test_no_errors_for_good_function(self):
        from agents.export_agent import _validate_convert_function

        def good_fn(examples):
            return json.dumps(examples)

        errors = _validate_convert_function(good_fn, [_make_example_dict()])
        assert errors == []

    def test_error_when_function_raises(self):
        from agents.export_agent import _validate_convert_function

        def bad_fn(examples):
            raise RuntimeError("conversion broken")

        errors = _validate_convert_function(bad_fn, [_make_example_dict()])
        assert len(errors) == 1
        assert "RuntimeError" in errors[0]

    def test_error_when_returns_non_string(self):
        from agents.export_agent import _validate_convert_function

        def dict_fn(examples):
            return {"wrapped": examples}  # returns dict, not str

        errors = _validate_convert_function(dict_fn, [_make_example_dict()])
        assert len(errors) == 1
        assert "dict" in errors[0]

    def test_error_when_returns_empty_string(self):
        from agents.export_agent import _validate_convert_function

        def empty_fn(examples):
            return ""

        errors = _validate_convert_function(empty_fn, [_make_example_dict()])
        assert len(errors) == 1
        assert "empty" in errors[0]

    def test_no_errors_for_empty_input(self):
        """Empty examples list should still produce a valid (possibly minimal) string."""
        from agents.export_agent import _validate_convert_function

        def fn(examples):
            return "[]"

        errors = _validate_convert_function(fn, [])
        assert errors == []


# ---------------------------------------------------------------------------
# _examples_to_dicts
# ---------------------------------------------------------------------------


class TestExamplesToDicts:
    """Tests for the _examples_to_dicts helper."""

    def test_converts_orm_objects_to_dicts(self):
        from agents.export_agent import _examples_to_dicts

        examples = [_make_orm_example(1), _make_orm_example(2)]
        result = _examples_to_dicts(examples)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["question"] == "ORM question 1?"
        assert result[0]["answer"] == "ORM answer 1"
        assert result[0]["choices"] is None

    def test_includes_dataset_name_when_present(self):
        from agents.export_agent import _examples_to_dicts

        examples = [_make_orm_example(1, with_dataset=True)]
        result = _examples_to_dicts(examples)

        assert result[0]["dataset_name"] == "MMLU"

    def test_includes_metadata_when_present(self):
        from agents.export_agent import _examples_to_dicts

        examples = [_make_orm_example(1, with_metadata=True)]
        result = _examples_to_dicts(examples)

        assert "metadata" in result[0]
        assert result[0]["metadata"]["subject"] == "math"

    def test_omits_metadata_key_when_none(self):
        from agents.export_agent import _examples_to_dicts

        examples = [_make_orm_example(1, with_metadata=False)]
        result = _examples_to_dicts(examples)

        assert "metadata" not in result[0]

    def test_returns_empty_list_for_empty_input(self):
        from agents.export_agent import _examples_to_dicts

        assert _examples_to_dicts([]) == []

    def test_converts_multiple_examples(self):
        from agents.export_agent import _examples_to_dicts

        examples = [_make_orm_example(i) for i in range(1, 6)]
        result = _examples_to_dicts(examples)

        assert len(result) == 5
        ids = [r["id"] for r in result]
        assert ids == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# ExportAgent.generate_converter
# ---------------------------------------------------------------------------


class TestGenerateConverter:
    """Tests for ExportAgent.generate_converter."""

    def test_returns_export_plan_on_valid_response(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=_sample_convert_response()):
            plan = agent.generate_converter("custom JSONL format")

        assert plan is not None
        assert plan.file_extension == ".json"
        assert plan.content_type == "application/json"
        assert "def convert" in plan.convert_function_code

    def test_returns_none_when_llm_fails(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=None):
            plan = agent.generate_converter("some format")

        assert plan is None

    def test_returns_none_on_invalid_json(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value="not valid json"):
            plan = agent.generate_converter("some format")

        assert plan is None

    def test_returns_none_when_convert_function_key_missing(self):
        from agents.export_agent import ExportAgent

        bad_response = json.dumps({"file_extension": ".txt", "explanation": "no function"})
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=bad_response):
            plan = agent.generate_converter("some format")

        assert plan is None

    def test_strips_fences_from_llm_response(self):
        from agents.export_agent import ExportAgent

        fenced = f"```json\n{_sample_convert_response()}\n```"
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=fenced):
            plan = agent.generate_converter("custom format")

        assert plan is not None

    def test_inspect_ai_hint_appended_to_prompt(self):
        """When 'inspect' appears in description, INSPECT_AI_HINT should be in the prompt."""
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        captured_prompts = []

        def capture_prompt(prompt):
            captured_prompts.append(prompt)
            return _sample_convert_response()

        with patch("agents.export_agent._call_gemini", side_effect=capture_prompt):
            agent.generate_converter("Export to Inspect AI format")

        assert captured_prompts
        assert "Inspect AI" in captured_prompts[0] or "input" in captured_prompts[0]

    def test_langsmith_hint_appended_to_prompt(self):
        """When 'langsmith' appears in description, LANGSMITH_HINT should be in the prompt."""
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        captured_prompts = []

        def capture_prompt(prompt):
            captured_prompts.append(prompt)
            return _sample_convert_response()

        with patch("agents.export_agent._call_gemini", side_effect=capture_prompt):
            agent.generate_converter("Export for LangSmith evaluation")

        assert captured_prompts
        assert "inputs" in captured_prompts[0] or "LangSmith" in captured_prompts[0]

    def test_eleuther_hint_appended_to_prompt(self):
        """When 'eleuther' appears in description, ELEUTHER_HARNESS_HINT should be in the prompt."""
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        captured_prompts = []

        def capture_prompt(prompt):
            captured_prompts.append(prompt)
            return _sample_convert_response()

        with patch("agents.export_agent._call_gemini", side_effect=capture_prompt):
            agent.generate_converter("Export for EleutherAI harness")

        assert captured_prompts
        assert "doc_id" in captured_prompts[0] or "EleutherAI" in captured_prompts[0]

    def test_no_hint_for_unknown_platform(self):
        """Unknown platform descriptions should not include any special hint in the prompt."""
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        captured_prompts = []

        def capture_prompt(prompt):
            captured_prompts.append(prompt)
            return _sample_convert_response()

        with patch("agents.export_agent._call_gemini", side_effect=capture_prompt):
            agent.generate_converter("Export to some custom weird format")

        assert captured_prompts
        # None of the known platform hints should appear
        assert "doc_id" not in captured_prompts[0]
        assert "LangSmith" not in captured_prompts[0]

    def test_default_file_extension_when_missing(self):
        """When file_extension is absent from LLM response, default .txt is used."""
        from agents.export_agent import ExportAgent

        response = json.dumps(
            {
                "convert_function": _sample_convert_code(),
                "explanation": "no extension provided",
                # no file_extension key
            }
        )
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=response):
            plan = agent.generate_converter("unknown format")

        assert plan is not None
        assert plan.file_extension == ".txt"

    def test_lm_eval_keyword_triggers_eleuther_hint(self):
        """The 'lm-eval' keyword should also trigger the EleutherAI hint."""
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        captured_prompts = []

        def capture_prompt(prompt):
            captured_prompts.append(prompt)
            return _sample_convert_response()

        with patch("agents.export_agent._call_gemini", side_effect=capture_prompt):
            agent.generate_converter("format for lm-eval harness")

        assert captured_prompts
        assert "doc_id" in captured_prompts[0] or "gold" in captured_prompts[0]


# ---------------------------------------------------------------------------
# ExportAgent.export — custom format
# ---------------------------------------------------------------------------


class TestExportCustomFormat:
    """Tests for ExportAgent.export with LLM-generated converters."""

    def _examples(self, n: int = 3) -> list[dict]:
        return [_make_example_dict(i) for i in range(1, n + 1)]

    def test_full_success_custom_format(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=_sample_convert_response()):
            result = agent.export(self._examples(), format_description="pretty JSON")

        assert result.success is True
        assert result.content  # Non-empty
        assert result.num_examples == 3
        assert result.plan is not None
        assert result.errors == []

    def test_failure_when_llm_fails(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=None):
            result = agent.export(self._examples(), format_description="some format")

        assert result.success is False
        assert any("llm" in e.lower() or "converter" in e.lower() for e in result.errors)

    def test_failure_when_compile_fails(self):
        from agents.export_agent import ExportAgent

        bad_response = json.dumps(
            {
                "convert_function": "def convert(\n  syntax error!!!",
                "file_extension": ".txt",
                "content_type": "text/plain",
                "explanation": "",
            }
        )
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=bad_response):
            result = agent.export(self._examples(), format_description="broken format")

        assert result.success is False
        assert any("compile" in e.lower() for e in result.errors)

    def test_failure_when_validation_fails(self):
        from agents.export_agent import ExportAgent

        invalid_response = json.dumps(
            {
                "convert_function": "def convert(examples):\n    return 42  # not a string\n",
                "file_extension": ".txt",
                "content_type": "text/plain",
                "explanation": "",
            }
        )
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=invalid_response):
            result = agent.export(self._examples(), format_description="bad format")

        assert result.success is False
        assert any("validation" in e.lower() for e in result.errors)

    def test_failure_when_convert_raises_at_runtime(self):
        from agents.export_agent import ExportAgent

        crashing_response = json.dumps(
            {
                "convert_function": (
                    "def convert(examples):\n"
                    "    if len(examples) > 2:\n"
                    "        raise RuntimeError('too many')\n"
                    "    return str(examples)\n"
                ),
                "file_extension": ".txt",
                "content_type": "text/plain",
                "explanation": "",
            }
        )
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=crashing_response):
            result = agent.export(self._examples(n=5), format_description="crashing format")

        assert result.success is False
        assert any("conversion" in e.lower() or "failed" in e.lower() for e in result.errors)

    def test_orm_objects_converted_to_dicts(self):
        """ORM-like objects (with .question attribute) should be converted before exporting."""
        from agents.export_agent import ExportAgent

        orm_examples = [_make_orm_example(i, with_dataset=True) for i in range(1, 4)]
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=_sample_convert_response()):
            result = agent.export(orm_examples, format_description="JSON output")

        assert result.success is True
        assert result.num_examples == 3

    def test_dataset_names_injected_into_example_dicts(self):
        """dataset_names mapping should be injected into dicts lacking dataset_name."""
        from agents.export_agent import ExportAgent

        examples = [_make_example_dict(1, dataset_id=7), _make_example_dict(2, dataset_id=7)]
        dataset_names = {7: "MMLU"}

        def capturing_convert(prompt):
            return json.dumps(
                {
                    "convert_function": (
                        "def convert(examples):\n"
                        "    import json as _j\n"
                        "    return _j.dumps(examples)\n"
                    ),
                    "file_extension": ".json",
                    "content_type": "application/json",
                    "explanation": "",
                }
            )

        agent = ExportAgent()
        # Use a custom format description that is not in BUILTIN_FORMATS so the
        # LLM path is taken (not the pre-built exporter which does not accept dicts).
        with patch("agents.export_agent._call_gemini", side_effect=capturing_convert):
            result = agent.export(
                examples,
                format_description="custom JSON output",
                dataset_names=dataset_names,
            )

        assert result.success is True
        # The content should include the injected dataset name
        assert "MMLU" in result.content

    def test_num_examples_matches_input_length(self):
        from agents.export_agent import ExportAgent

        examples = self._examples(n=7)
        agent = ExportAgent()
        with patch("agents.export_agent._call_gemini", return_value=_sample_convert_response()):
            result = agent.export(examples, format_description="JSON")

        assert result.num_examples == 7


# ---------------------------------------------------------------------------
# ExportAgent.export — builtin format delegation
# ---------------------------------------------------------------------------


class TestExportBuiltinFormats:
    """Tests for ExportAgent.export when format_description is a builtin format."""

    def _examples(self, n: int = 3) -> list[dict]:
        return [_make_example_dict(i) for i in range(1, n + 1)]

    def test_json_format_delegates_to_to_json(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        mock_content = '[{"id": 1, "question": "Q?"}]'
        with patch("core.export.formats.to_json", return_value=mock_content) as mock_fn:
            result = agent.export(self._examples(), format_description="json")

        assert result.success is True
        assert result.content == mock_content
        assert result.file_extension == ".json"
        assert result.content_type == "application/json"
        assert result.plan is None
        mock_fn.assert_called_once()

    def test_jsonl_format_delegates_to_to_jsonl(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        mock_content = '{"id": 1}\n{"id": 2}\n'
        with patch("core.export.formats.to_jsonl", return_value=mock_content) as mock_fn:
            result = agent.export(self._examples(), format_description="jsonl")

        assert result.success is True
        assert result.content == mock_content
        assert result.file_extension == ".jsonl"
        assert result.content_type == "application/x-ndjson"
        mock_fn.assert_called_once()

    def test_csv_format_delegates_to_to_csv(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        mock_content = "id,question,answer\n1,Q?,A\n"
        with patch("core.export.formats.to_csv", return_value=mock_content) as mock_fn:
            result = agent.export(self._examples(), format_description="csv")

        assert result.success is True
        assert result.content == mock_content
        assert result.file_extension == ".csv"
        assert result.content_type == "text/csv"
        mock_fn.assert_called_once()

    def test_builtin_format_does_not_call_llm(self):
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with (
            patch("core.export.formats.to_json", return_value="[]"),
            patch("agents.export_agent._call_gemini") as mock_llm,
        ):
            agent.export(self._examples(), format_description="json")

        mock_llm.assert_not_called()

    def test_builtin_format_case_insensitive(self):
        """'JSON' (uppercase) should still be recognised as the json builtin."""
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with patch("core.export.formats.to_json", return_value="[]") as mock_fn:
            result = agent.export(self._examples(), format_description="JSON")

        assert result.success is True
        mock_fn.assert_called_once()

    def test_builtin_failure_returns_error_result(self):
        """If the pre-built exporter raises, ExportResult should report failure."""
        from agents.export_agent import ExportAgent

        agent = ExportAgent()
        with patch("core.export.formats.to_json", side_effect=RuntimeError("serialise error")):
            result = agent.export(self._examples(), format_description="json")

        assert result.success is False
        assert any("builtin" in e.lower() or "failed" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# ExportPlan / ExportResult dataclasses
# ---------------------------------------------------------------------------


class TestExportDataclasses:
    """Tests for ExportPlan and ExportResult dataclasses."""

    def test_export_result_defaults(self):
        from agents.export_agent import ExportResult

        result = ExportResult(
            success=True,
            content="{}",
            file_extension=".json",
            content_type="application/json",
            plan=None,
            num_examples=5,
        )
        assert result.errors == []

    def test_export_plan_fields(self):
        from agents.export_agent import ExportPlan

        plan = ExportPlan(
            format_description="custom JSON",
            convert_function_code=_sample_convert_code(),
            file_extension=".json",
            content_type="application/json",
            explanation="Simple JSON dump",
        )
        assert plan.format_description == "custom JSON"
        assert plan.file_extension == ".json"
        assert "def convert" in plan.convert_function_code

    def test_export_result_with_errors(self):
        from agents.export_agent import ExportResult

        result = ExportResult(
            success=False,
            content="",
            file_extension=".txt",
            content_type="text/plain",
            plan=None,
            num_examples=0,
            errors=["LLM failed", "compile failed"],
        )
        assert len(result.errors) == 2
        assert result.success is False


# ---------------------------------------------------------------------------
# BUILTIN_FORMATS constant
# ---------------------------------------------------------------------------


class TestBuiltinFormatsConstant:
    """Tests that BUILTIN_FORMATS is correctly defined."""

    def test_builtin_formats_contains_expected_values(self):
        from agents.export_agent import BUILTIN_FORMATS

        assert "json" in BUILTIN_FORMATS
        assert "jsonl" in BUILTIN_FORMATS
        assert "csv" in BUILTIN_FORMATS
        assert "langfuse" in BUILTIN_FORMATS

    def test_builtin_formats_is_set(self):
        from agents.export_agent import BUILTIN_FORMATS

        assert isinstance(BUILTIN_FORMATS, (set, frozenset))
