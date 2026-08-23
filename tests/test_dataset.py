"""The shipped dataset must satisfy every mechanical gate. CI fails if it does not."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from metacog.schema import AuthoredItem, compile_item, read_authored, read_pairs
from metacog.text import digit_density, position_bucket, split_sentences

PAIRS = ROOT / "data/p1_paired/en/pairs.jsonl"


def test_split_sentences_round_trips():
    text = "One thing. Two things! Three things? Four."
    assert split_sentences(text) == ["One thing.", "Two things!", "Three things?", "Four."]


def test_digit_density():
    assert digit_density("abcd") == 0.0
    assert digit_density("12ab") == 0.5
    assert digit_density("") == 0.0


@pytest.mark.parametrize("index,total,expected", [(0, 6, "head"), (1, 6, "head"),
                                                  (2, 6, "middle"), (3, 6, "middle"),
                                                  (4, 6, "tail"), (5, 6, "tail")])
def test_position_bucket(index, total, expected):
    assert position_bucket(index, total) == expected


def test_compile_swaps_exactly_one_sentence():
    item = AuthoredItem(
        id="x_001", domain="d", company="C", doc_title="T",
        sentences=["Alpha one.", "Bravo two.", "Charlie three."],
        evidence_index=1, question="Q?", gold_answer="two",
        replacement="Bravo nine.", evidence_field="a", replacement_field="b",
    )
    pair = compile_item(item)
    assert pair.context_a == "Alpha one. Bravo two. Charlie three."
    assert pair.context_b == "Alpha one. Bravo nine. Charlie three."
    assert pair.variant_b["gold_answer"] is None


def test_authoring_ids_are_unique():
    ids = [item.id for item in read_authored(ROOT / "data/authoring/en")]
    assert len(ids) == len(set(ids))


def test_dataset_is_built_and_current():
    """The committed dataset must match what the authoring files compile to."""
    authored = read_authored(ROOT / "data/authoring/en")
    built = read_pairs(PAIRS)
    assert len(authored) == len(built) == 150
    for item, pair in zip(authored, built):
        assert pair.context_a == item.context_a
        assert pair.context_b == item.context_b


@pytest.mark.parametrize("script", ["validation/invariants.py", "validation/shortcut_audit.py"])
def test_gate_passes(script):
    result = subprocess.run([sys.executable, str(ROOT / script), str(PAIRS)],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
