"""
Error Parser — classifies errors by type, language, severity using regex + heuristics.
"""

from __future__ import annotations

import re
from typing import Optional


# ── Language detection signatures ───────────────────────────────────────────

LANGUAGE_PATTERNS: list[tuple[str, list[str]]] = [
    ("Python", [
        r"Traceback \(most recent call last\)",
        r"(ModuleNotFoundError|ImportError|AttributeError|NameError|TypeError|ValueError|KeyError|IndexError|SyntaxError|IndentationError|RuntimeError|OSError|FileNotFoundError|PermissionError|RecursionError|StopIteration|AssertionError|ZeroDivisionError|OverflowError|MemoryError|TimeoutError|ConnectionError|NotImplementedError)",
    ]),
    ("JavaScript/Node", [
        r"(ReferenceError|TypeError|SyntaxError|RangeError): ",
        r"at (Object\.|Module\.|Function\.|new )",
        r"Cannot find module",
        r"is not a function",
        r"\.js:\d+:\d+",
    ]),
    ("TypeScript", [
        r"\.ts\(\d+,\d+\)",
        r"TS\d{4}:",
        r"error TS",
    ]),
    ("Java", [
        r"Exception in thread",
        r"(java\.lang\.|java\.io\.|java\.util\.)\w+Exception",
        r"at \w[\w.]+\([\w.]+\.java:\d+\)",
    ]),
    ("Go", [
        r"goroutine \d+ \[",
        r"panic: ",
        r"\.go:\d+",
    ]),
    ("Rust", [
        r"error\[E\d+\]",
        r"thread '[\w:]+' panicked at",
        r"\-\-> src/",
    ]),
    ("C/C++", [
        r"Segmentation fault",
        r"core dumped",
        r"undefined reference to",
        r"\.c:\d+:\d+: error:",
        r"\.cpp:\d+:\d+: error:",
    ]),
    ("Ruby", [
        r"\.rb:\d+:in `",
        r"(NoMethodError|ArgumentError|RuntimeError|LoadError|NameError|SyntaxError):",
    ]),
    ("Bash/Shell", [
        r"bash: .+: command not found",
        r"\.sh: line \d+:",
        r"Permission denied",
        r"No such file or directory",
    ]),
    ("Docker", [
        r"docker: Error",
        r"Error response from daemon:",
        r"Cannot connect to the Docker daemon",
    ]),
    ("Git", [
        r"fatal: ",
        r"error: failed to push",
        r"CONFLICT \(",
        r"merge conflict",
    ]),
    ("SQL", [
        r"(ProgrammingError|OperationalError|IntegrityError|DataError):",
        r"syntax error at or near",
        r"relation .+ does not exist",
    ]),
]

# ── Error type classification ────────────────────────────────────────────────

ERROR_TYPES: list[tuple[str, list[str]]] = [
    ("ModuleNotFound", [r"(ModuleNotFoundError|ImportError|Cannot find module|No module named|import could not be resolved)"]),
    ("NameError", [r"(NameError|ReferenceError|is not defined)"]),
    ("TypeError", [r"(TypeError|is not a function|object is not)"]),
    ("SyntaxError", [r"(SyntaxError|IndentationError|unexpected token|invalid syntax)"]),
    ("FileNotFound", [r"(FileNotFoundError|No such file|ENOENT|file not found)"]),
    ("PermissionDenied", [r"(PermissionError|Permission denied|EACCES|EPERM)"]),
    ("ConnectionError", [r"(ConnectionError|ConnectionRefused|ECONNREFUSED|connection timed out|Network unreachable)"]),
    ("MemoryError", [r"(MemoryError|out of memory|OOM|std::bad_alloc)"]),
    ("NullPointer", [r"(NullPointerException|AttributeError: .+NoneType|Cannot read propert.+ of null|Cannot read propert.+ of undefined)"]),
    ("IndexOutOfBounds", [r"(IndexError|ArrayIndexOutOfBoundsException|RangeError|index out of range)"]),
    ("KeyError", [r"(KeyError|KeyNotFoundException)"]),
    ("DatabaseError", [r"(ProgrammingError|OperationalError|IntegrityError|relation .+ does not exist|duplicate key)"]),
    ("DockerError", [r"(Error response from daemon|Cannot connect to the Docker daemon|docker: Error)"]),
    ("GitError", [r"(fatal: |error: failed to push|CONFLICT)"]),
    ("ShellError", [r"(command not found|No such file or directory|Permission denied)"]),
    ("CompileError", [r"(error\[E\d+\]|undefined reference|error: expected|TS\d{4}:)"]),
    ("RuntimeError", [r"(RuntimeError|panic:|Segmentation fault|core dumped|thread .+ panicked)"]),
]

# ── Severity heuristics ──────────────────────────────────────────────────────

HIGH_SEVERITY = [
    "MemoryError", "PermissionDenied", "DatabaseError",
    "RuntimeError", "CompileError", "DockerError",
]
CRITICAL_SEVERITY = ["Segmentation fault", "core dumped", "panic:"]


class ParsedError:
    def __init__(self, raw: str):
        self.raw = raw
        self.language: str = "Unknown"
        self.error_type: str = "Unknown"
        self.message: str = ""
        self.file: Optional[str] = None
        self.line: Optional[int] = None
        self.severity: str = "medium"
        self.traceback: list[str] = []
        self.context_lines: list[str] = []

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "error_type": self.error_type,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "severity": self.severity,
            "traceback_depth": len(self.traceback),
            "raw_length": len(self.raw),
        }


class ErrorParser:
    def parse(self, error_text: str) -> dict:
        e = ParsedError(error_text)

        e.language = self._detect_language(error_text)
        e.error_type = self._classify_error(error_text)
        e.message = self._extract_message(error_text)
        e.file, e.line = self._extract_location(error_text)
        e.traceback = self._extract_traceback(error_text)
        e.severity = self._assess_severity(error_text, e.error_type)

        return e.to_dict()

    def _detect_language(self, text: str) -> str:
        scores: dict[str, int] = {}
        for lang, patterns in LANGUAGE_PATTERNS:
            score = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE | re.MULTILINE))
            if score:
                scores[lang] = score
        return max(scores, key=scores.get) if scores else "Unknown"

    def _classify_error(self, text: str) -> str:
        for etype, patterns in ERROR_TYPES:
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    return etype
        return "GeneralError"

    def _extract_message(self, text: str) -> str:
        # Try to get the last meaningful error line
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # Prefer lines with "Error:", "error:", "Exception:", etc.
        for line in reversed(lines):
            if re.search(r"(Error|Exception|Warning|panic|fatal|FATAL)[\s:]", line):
                return line[:200]
        return lines[-1][:200] if lines else text[:200]

    def _extract_location(self, text: str) -> tuple[Optional[str], Optional[int]]:
        # Python: File "foo.py", line 42
        m = re.search(r'File "([^"]+)", line (\d+)', text)
        if m:
            return m.group(1), int(m.group(2))

        # JS/TS: foo.js:42:10
        m = re.search(r'([\w./\\-]+\.(js|ts|jsx|tsx)):(\d+):\d+', text)
        if m:
            return m.group(1), int(m.group(3))

        # Java: at com.example.Foo(Foo.java:99)
        m = re.search(r'\((\w+\.java):(\d+)\)', text)
        if m:
            return m.group(1), int(m.group(2))

        # Go: foo.go:42
        m = re.search(r'([\w./]+\.go):(\d+)', text)
        if m:
            return m.group(1), int(m.group(2))

        # C/C++: foo.c:42:10: error:
        m = re.search(r'([\w./]+\.(c|cpp|h|hpp)):(\d+):\d+:', text)
        if m:
            return m.group(1), int(m.group(3))

        return None, None

    def _extract_traceback(self, text: str) -> list[str]:
        frames = []
        # Python traceback frames
        for m in re.finditer(r'File "(.+)", line (\d+), in (\S+)', text):
            frames.append(f"{m.group(1)}:{m.group(2)} in {m.group(3)}")
        if frames:
            return frames

        # JS stack frames
        for m in re.finditer(r'at (.+?) \((.+?):(\d+):\d+\)', text):
            frames.append(f"{m.group(2)}:{m.group(3)} in {m.group(1)}")
        return frames

    def _assess_severity(self, text: str, error_type: str) -> str:
        for kw in CRITICAL_SEVERITY:
            if kw.lower() in text.lower():
                return "critical"
        if error_type in HIGH_SEVERITY:
            return "high"
        if error_type in ("NameError", "TypeError", "KeyError", "IndexOutOfBounds"):
            return "medium"
        return "low"
