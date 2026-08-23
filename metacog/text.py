"""Text utilities shared by the builder, the validators and the tests."""

from __future__ import annotations

import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    """Split on sentence-final punctuation followed by whitespace.

    Deliberately simple. The authored corpus is written so that this rule is exact,
    which lets ``invariants`` assert that variants A and B differ in exactly one
    sentence without any fuzzy matching.
    """
    return [s for s in _SENTENCE_BOUNDARY.split(text.strip()) if s]


def digit_density(text: str) -> float:
    """Fraction of characters that are digits.

    Guards rule 3 of the B-variant contract: the replacement proposition must carry
    a comparable amount of numeric detail, otherwise a bag-of-words classifier can
    separate A from B without reading the question.
    """
    return sum(c.isdigit() for c in text) / max(len(text), 1)


def position_bucket(index: int, total: int) -> str:
    """Which third of the document a sentence falls in: head, middle or tail."""
    frac = index / max(total, 1)
    if frac < 1 / 3:
        return "head"
    if frac < 2 / 3:
        return "middle"
    return "tail"
