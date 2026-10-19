from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Keyword:
    """A parsed keyword, its alternatives, and its scoring weight."""

    text: str
    weight: int = 1

    @property
    def display(self) -> str:
        if self.weight == 1:
            return self.text
        return f"{self.text} ×{self.weight}"


def parse_keyword(entry: str) -> Keyword | None:
    """Parse one entry such as ``python``, ``python:3``, or ``js|javascript:2``.

    A positive integer suffix after the last colon is treated as a weight.
    Anything else (for example ``http://example``) stays part of the keyword.
    Empty entries and pipe-only entries return ``None``.
    """
    text = entry.strip()
    if not text:
        return None

    weight = 1
    base, separator, raw_weight = text.rpartition(":")
    if separator and base.strip() and raw_weight.strip().isdigit():
        text = base.strip()
        weight = max(1, int(raw_weight.strip()))

    alternatives = [alternative.strip() for alternative in text.split("|")]
    if not any(alternatives):
        return None
    return Keyword("|".join(alternatives), weight)


def parse_keywords(raw: str) -> list[Keyword]:
    """Split a comma-separated keyword string, trim, and de-duplicate.

    ``js|javascript`` stays a single entry: the pipe denotes alternatives.
    Duplicate keywords keep their first occurrence and weight.
    """
    seen: set[str] = set()
    keywords: list[Keyword] = []
    for part in raw.split(","):
        keyword = parse_keyword(part)
        if keyword is None:
            continue
        key = keyword.text.casefold()
        if key in seen:
            continue
        seen.add(key)
        keywords.append(keyword)
    return keywords


def _alternative_pattern(alternative: str) -> str:
    """Wrap one alternative in boundaries that respect ``C++``/``C#``/``.NET``.

    A leading word character needs a non-word character before it, which stops
    ``java`` matching inside ``javascript``.  An alternative that starts with
    punctuation (``.NET``) may follow a word character (``ASP.NET``).  The
    trailing guard stops ``C`` matching inside ``C++`` while still allowing a
    keyword that itself ends in ``+`` or ``#``.
    """
    escaped = re.escape(alternative)
    leading = r"(?<!\w)" if re.match(r"\w", alternative) else ""
    return f"{leading}{escaped}(?![\\w+#])"


@lru_cache(maxsize=512)
def _compile(keyword: str) -> re.Pattern[str] | None:
    alternatives = [alt.strip() for alt in keyword.split("|") if alt.strip()]
    if not alternatives:
        return None
    pattern = "|".join(_alternative_pattern(alt) for alt in alternatives)
    return re.compile(f"(?:{pattern})", re.IGNORECASE)


def _coerce_keyword(value: Keyword | str) -> Keyword:
    """Allow ``score`` to accept raw strings as well as parsed keywords."""
    if isinstance(value, Keyword):
        return value
    parsed = parse_keyword(value)
    return parsed if parsed is not None else Keyword(value, 1)


def score(
    text: str, keywords: Sequence[Keyword | str]
) -> tuple[float, list[str], list[str]]:
    """Return ``(percent, matched, missing)`` for ``text``.

    Percent is the share of total keyword weight that was found, rounded to one
    decimal place. With default weights this is the old keyword-count formula.
    """
    if not keywords:
        return 0.0, [], []

    parsed = [_coerce_keyword(keyword) for keyword in keywords]
    total_weight = sum(max(0, keyword.weight) for keyword in parsed)

    matched: list[str] = []
    missing: list[str] = []
    matched_weight = 0
    for keyword in parsed:
        pattern = _compile(keyword.text)
        if pattern is not None and pattern.search(text):
            matched.append(keyword.display)
            matched_weight += max(0, keyword.weight)
        else:
            missing.append(keyword.display)

    percent = (
        round(matched_weight / total_weight * 100, 1) if total_weight else 0.0
    )
    return percent, matched, missing


def qualifies(percent: float | None, threshold: float) -> bool:
    """A resume qualifies when it is readable and at or above ``threshold``."""
    return percent is not None and percent >= threshold
