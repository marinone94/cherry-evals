"""Tests for core.safety.output_scanner — credential leak and secret detection."""

from core.safety.output_scanner import redact_secrets, sanitize_error_message, scan_for_leaks


class TestScanForLeaks:
    def test_detects_api_key(self):
        text = "Error connecting with key sk-abc123def456ghi789jkl012mno"
        findings = scan_for_leaks(text)
        assert any(f["type"] == "credential:api_key" for f in findings)

    def test_detects_aws_key(self):
        text = "Configured with AKIAIOSFODNN7EXAMPLE"
        findings = scan_for_leaks(text)
        assert any(f["type"] == "credential:aws_key" for f in findings)

    def test_detects_github_token(self):
        text = "Using token ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        findings = scan_for_leaks(text)
        assert any(f["type"] == "credential:github_token" for f in findings)

    def test_detects_connection_string(self):
        text = "postgres://user:pass@db.internal.example.com:5432/mydb"
        findings = scan_for_leaks(text)
        assert any(f["type"] == "credential:connection_string" for f in findings)

    def test_detects_internal_host(self):
        text = "Failed to connect to 192.168.1.100:5432"
        findings = scan_for_leaks(text)
        assert any(f["type"] == "infra:internal_host" for f in findings)

    def test_detects_stack_trace(self):
        text = "Traceback (most recent call last):\n  File \"/app/main.py\", line 42"
        findings = scan_for_leaks(text)
        assert any(f["type"] == "infra:stack_trace" for f in findings)

    def test_clean_text(self):
        text = "Export completed successfully with 42 examples."
        findings = scan_for_leaks(text)
        assert findings == []


class TestRedactSecrets:
    def test_redacts_api_key(self):
        text = "Key: sk-abc123def456ghi789jkl012mno"
        result = redact_secrets(text)
        assert "sk-abc" not in result
        assert "[REDACTED:api_key]" in result

    def test_preserves_normal_text(self):
        text = "Export completed."
        assert redact_secrets(text) == text


class TestSanitizeErrorMessage:
    def test_returns_generic_for_credential_leak(self):
        error = "Auth failed: postgres://user:pass@db.internal:5432/app"
        result = sanitize_error_message(error)
        assert result == "An internal error occurred."

    def test_redacts_internal_hosts(self):
        error = "Connection refused to 192.168.1.100:6333"
        result = sanitize_error_message(error)
        assert "192.168" not in result
        assert "[internal_host]" in result

    def test_redacts_stack_traces(self):
        error = "Traceback (most recent call last):\n  lots of text"
        result = sanitize_error_message(error)
        assert "Traceback" not in result

    def test_truncates_long_errors(self):
        error = "x" * 1000
        result = sanitize_error_message(error)
        assert len(result) <= 504  # 500 + "..."

    def test_preserves_safe_errors(self):
        error = "Collection not found"
        assert sanitize_error_message(error) == error

    def test_accepts_exception_objects(self):
        error = ValueError("bad value")
        result = sanitize_error_message(error)
        assert "bad value" in result


class TestRestrictedBuiltins:
    """Verify that LLM-generated code exec uses restricted builtins."""

    def test_export_compile_blocks_open(self):
        from agents.export_agent import _compile_convert_function

        code = "def convert(examples):\n    return open('/etc/passwd').read()"
        fn = _compile_convert_function(code)
        # Either compilation fails (returns None) or execution raises
        if fn is not None:
            import pytest

            with pytest.raises((NameError, TypeError)):
                fn([])

    def test_export_compile_blocks_import(self):
        from agents.export_agent import _compile_convert_function

        code = "import os\ndef convert(examples):\n    return os.getcwd()"
        fn = _compile_convert_function(code)
        assert fn is None  # import not available, should fail to compile

    def test_export_compile_blocks_eval(self):
        from agents.export_agent import _compile_convert_function

        code = "def convert(examples):\n    return eval('1+1')"
        fn = _compile_convert_function(code)
        if fn is not None:
            import pytest

            with pytest.raises((NameError, TypeError)):
                fn([])

    def test_export_compile_allows_safe_code(self):
        from agents.export_agent import _compile_convert_function

        # json is pre-injected via safe_globals, not imported
        code = (
            "def convert(examples):\n"
            "    return json.dumps([{'q': e.get('question', '')} for e in examples])"
        )
        fn = _compile_convert_function(code)
        assert fn is not None
        result = fn([{"question": "What is 2+2?"}])
        assert "What is 2+2?" in result

    def test_ingestion_compile_blocks_open(self):
        from agents.ingestion_agent import _compile_parse_function

        code = "def parse_row(row, dataset_id, split):\n    return open('/etc/passwd').read()"
        fn = _compile_parse_function(code)
        if fn is not None:
            import pytest

            with pytest.raises((NameError, TypeError)):
                fn({}, 1, "train")

    def test_ingestion_compile_blocks_import(self):
        from agents.ingestion_agent import _compile_parse_function

        code = "import os\ndef parse_row(row, dataset_id, split):\n    return {}"
        fn = _compile_parse_function(code)
        assert fn is None


class TestOutputScannerWiring:
    """Verify output scanner is wired into agent error paths."""

    def test_export_agent_imports_sanitize_error_message(self):
        import agents.export_agent as mod

        assert hasattr(mod, "sanitize_error_message")

    def test_ingestion_agent_imports_sanitize_error_message(self):
        import agents.ingestion_agent as mod

        assert hasattr(mod, "sanitize_error_message")

    def test_sanitize_error_message_redacts_connection_string(self):
        from core.safety.output_scanner import sanitize_error_message

        error_msg = sanitize_error_message(
            ValueError("postgres://user:pass@db.internal:5432/app")
        )
        assert error_msg == "An internal error occurred."
