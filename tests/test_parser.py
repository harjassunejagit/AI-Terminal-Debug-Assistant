"""
Tests for the error parser module.
"""

import pytest
from src.parsers.error_parser import ErrorParser


@pytest.fixture
def parser():
    return ErrorParser()


# ── Language Detection ────────────────────────────────────────────────────────

def test_detects_python(parser):
    error = """Traceback (most recent call last):
  File "app.py", line 3, in <module>
    import dotenv
ModuleNotFoundError: No module named 'dotenv'"""
    result = parser.parse(error)
    assert result["language"] == "Python"


def test_detects_javascript(parser):
    error = """TypeError: Cannot read properties of undefined (reading 'map')
    at App (/home/user/project/src/App.js:42:15)
    at renderWithHooks (/node_modules/react-dom/cjs/react-dom.development.js:14985:18)"""
    result = parser.parse(error)
    assert "JavaScript" in result["language"]


def test_detects_java(parser):
    error = """Exception in thread "main" java.lang.NullPointerException
    at com.example.Main.run(Main.java:25)
    at com.example.Main.main(Main.java:10)"""
    result = parser.parse(error)
    assert result["language"] == "Java"


def test_detects_docker(parser):
    error = "Error response from daemon: Cannot connect to the Docker daemon at unix:///var/run/docker.sock"
    result = parser.parse(error)
    assert result["language"] == "Docker"


# ── Error Type Classification ─────────────────────────────────────────────────

def test_classifies_module_not_found(parser):
    error = "ModuleNotFoundError: No module named 'requests'"
    result = parser.parse(error)
    assert result["error_type"] == "ModuleNotFound"


def test_classifies_name_error(parser):
    error = "NameError: name 'my_var' is not defined"
    result = parser.parse(error)
    assert result["error_type"] == "NameError"


def test_classifies_syntax_error(parser):
    error = "SyntaxError: invalid syntax"
    result = parser.parse(error)
    assert result["error_type"] == "SyntaxError"


def test_classifies_file_not_found(parser):
    error = "FileNotFoundError: [Errno 2] No such file or directory: 'config.json'"
    result = parser.parse(error)
    assert result["error_type"] == "FileNotFound"


def test_classifies_permission_error(parser):
    error = "PermissionError: [Errno 13] Permission denied: '/etc/hosts'"
    result = parser.parse(error)
    assert result["error_type"] == "PermissionDenied"


def test_classifies_connection_error(parser):
    error = "ConnectionRefusedError: [Errno 111] Connection refused"
    result = parser.parse(error)
    assert result["error_type"] == "ConnectionError"


# ── Location Extraction ───────────────────────────────────────────────────────

def test_extracts_python_file_and_line(parser):
    error = 'File "src/main.py", line 42, in run\n    result = do_thing()'
    result = parser.parse(error)
    assert result["file"] == "src/main.py"
    assert result["line"] == 42


def test_extracts_js_file_and_line(parser):
    error = "TypeError: x is not a function\n    at Object.<anonymous> (index.js:10:5)"
    result = parser.parse(error)
    assert result["file"] == "index.js"
    assert result["line"] == 10


# ── Severity Assessment ───────────────────────────────────────────────────────

def test_severity_low_for_name_error(parser):
    result = parser.parse("NameError: name 'x' is not defined")
    assert result["severity"] in ("low", "medium")


def test_severity_critical_for_segfault(parser):
    result = parser.parse("Segmentation fault (core dumped)")
    assert result["severity"] == "critical"


# ── Edge Cases ────────────────────────────────────────────────────────────────

def test_handles_empty_string(parser):
    result = parser.parse("")
    assert "language" in result
    assert "error_type" in result


def test_handles_non_error_text(parser):
    result = parser.parse("Hello, world! Everything is fine.")
    assert result["language"] == "Unknown"


def test_traceback_extraction(parser):
    error = """Traceback (most recent call last):
  File "a.py", line 1, in <module>
    from b import foo
  File "b.py", line 5, in <module>
    from c import bar
ImportError: cannot import name 'bar' from 'c'"""
    result = parser.parse(error)
    assert result["traceback_depth"] == 2
