"""Dataset schema and I/O for Pillar 1 paired-twin items.

Two representations exist and they serve different purposes:

* **Authoring form** (``data/authoring/<lang>/<domain>.jsonl``) — what a human edits.
  A document is a *list of sentences*, and variant B is expressed as a single
  ``replacement`` string plus the index it overwrites. This makes the "exactly one
  sentence differs" invariant true by construction rather than by inspection.

* **Release form** (``data/p1_paired/<lang>/pairs.jsonl``) — what gets evaluated and
  published, following §8.1 of the design spec.

``build_pairs.py`` compiles the first into the second.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .text import position_bucket, split_sentences

REPLACEMENT_STRATEGY = "same_topic_different_field"


@dataclass(frozen=True)
class AuthoredItem:
    """One hand-written twin pair, in authoring form."""

    id: str
    domain: str
    company: str
    doc_title: str
    sentences: list[str]
    evidence_index: int
    question: str
    gold_answer: str
    replacement: str
    evidence_field: str
    replacement_field: str
    # Alternative phrasings that also count as correct. Needed where the gold answer is
    # a long phrase a correct answer may legitimately shorten. Most items need none:
    # `scoring.accepted_forms` already strips leading qualifiers such as "every".
    answer_aliases: tuple[str, ...] = ()

    @property
    def evidence(self) -> str:
        return self.sentences[self.evidence_index]

    @property
    def context_a(self) -> str:
        return " ".join(self.sentences)

    @property
    def context_b(self) -> str:
        swapped = list(self.sentences)
        swapped[self.evidence_index] = self.replacement
        return " ".join(swapped)

    @property
    def position(self) -> str:
        return position_bucket(self.evidence_index, len(self.sentences))


@dataclass
class Pair:
    """One twin pair in release form (design spec §8.1)."""

    pair_id: str
    question: str
    variant_a: dict[str, Any]
    variant_b: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def context_a(self) -> str:
        return " ".join(c["text"] for c in self.variant_a["contexts"])

    @property
    def context_b(self) -> str:
        return " ".join(c["text"] for c in self.variant_b["contexts"])

    @property
    def gold_answer(self) -> str:
        return self.variant_a["gold_answer"]

    def to_json(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "question": self.question,
            "variant_a": self.variant_a,
            "variant_b": self.variant_b,
            "meta": self.meta,
        }


def read_authored(directory: str | Path) -> list[AuthoredItem]:
    """Load every ``*.jsonl`` under ``directory`` as authoring-form items."""
    items: list[AuthoredItem] = []
    for path in sorted(Path(directory).glob("*.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                items.append(AuthoredItem(**json.loads(line)))
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return items


def read_pairs(path: str | Path) -> list[Pair]:
    """Load release-form pairs."""
    pairs = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            pairs.append(Pair(**json.loads(line)))
    return pairs


def write_pairs(path: str | Path, pairs: Iterator[Pair]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(pair.to_json(), ensure_ascii=False) + "\n")
            count += 1
    return count


def compile_item(item: AuthoredItem, lang: str = "en") -> Pair:
    """Turn an authored item into a release-form pair."""
    sentences = split_sentences(item.context_a)
    return Pair(
        pair_id=f"p1_{lang}_{item.id}",
        question=item.question,
        variant_a={
            "contexts": [{"chunk_id": "c1", "text": item.context_a}],
            "gold_answer": item.gold_answer,
            "answer_aliases": list(item.answer_aliases),
            "evidence_chunk_id": "c1",
        },
        variant_b={
            "contexts": [{"chunk_id": "c1", "text": item.context_b}],
            "gold_answer": None,
            "removed_proposition": item.evidence,
            "replacement_proposition": item.replacement,
            "replacement_strategy": REPLACEMENT_STRATEGY,
        },
        meta={
            "domain": item.domain,
            "lang": lang,
            "company": item.company,
            "doc_title": item.doc_title,
            "n_distractors": 0,
            "n_sentences": len(sentences),
            "evidence_sentence_index": item.evidence_index,
            "evidence_position": item.position,
            "evidence_field": item.evidence_field,
            "replacement_field": item.replacement_field,
            "char_len_a": len(item.context_a),
            "char_len_b": len(item.context_b),
            "source": "authored",
        },
    )
