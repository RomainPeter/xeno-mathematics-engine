"""Input sanitisation helpers used by tests."""

from __future__ import annotations

import re

MAX_LENGTH = 1000
_SQL_KEYWORDS = {"drop", "table", "insert", "delete", "update"}


def sanitize_input(text: str | None) -> str:
    if text is None:
        return ""

    escaped = re.escape(text)
    trimmed = escaped[:MAX_LENGTH]

    pattern = re.compile(r"|".join(_SQL_KEYWORDS), re.IGNORECASE)
    sanitised = pattern.sub("", trimmed)
    sanitised = sanitised.replace("@", "\\@")
    return sanitised


_EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_email(email: str) -> bool:
    return bool(_EMAIL_REGEX.match(email or ""))


_SCRIPT_STYLE_REGEX = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def clean_html(html: str) -> str:
    cleaned = _SCRIPT_STYLE_REGEX.sub("", html or "")
    return cleaned


def escape_sql(value: str) -> str:
    if value is None:
        return ""
    value = value.replace("'", "''")
    value = value.replace(";", "")
    value = value.replace("--", "")
    value = value.replace("/*", "").replace("*/", "")
    return value
