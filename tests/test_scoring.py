"""GATE 4 scorer: behaviour classification, answer grading, agreement statistics."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.scoring import (Behaviour, BehaviourScorer, accepted_forms, cohens_kappa,
                             is_correct)

scorer = BehaviourScorer()


@pytest.mark.parametrize("output,expected,tier", [
    ("NO INFORMATION", Behaviour.ABSTAIN, 1),
    ("NO INFORMATION.", Behaviour.ABSTAIN, 1),
    ("  no information  ", Behaviour.ABSTAIN, 1),
    ("60 days", Behaviour.ANSWER, 2),
    ("The maximum probation period is 60 days.", Behaviour.ANSWER, 2),
    ("The document does not state the probation period.", Behaviour.ABSTAIN, 2),
    ("There is no information about this in the passage.", Behaviour.ABSTAIN, 2),
    ("It might be 45 days, but the text is unclear.", Behaviour.HEDGE, 2),
    ("", Behaviour.HEDGE, 1),
])
def test_behaviour(output, expected, tier):
    label = scorer(output)
    assert label.behaviour is expected
    assert label.tier == tier


def test_refusal_plus_figure_is_a_hedge_not_an_abstention():
    """Counting this as abstention would inflate DAS, which is the error Pillar 1
    exists to expose."""
    text = "The document does not state the probation period, but it mentions 45 days."
    assert scorer(text).behaviour is Behaviour.HEDGE


@pytest.mark.parametrize("output,gold,expected", [
    ("60 days", "60 days", True),
    ("The answer is 60 days.", "60 days", True),
    ("Every six months.", "every 6 months", True),      # spelled-out number
    ("6 months", "every 6 months", True),               # qualifier dropped
    ("7 hours", "longer than 7 hours", True),
    ("45 days", "60 days", False),
    ("160 days", "60 days", False),                     # substring must not match
    ("60 months", "60 days", False),                    # unit must survive
    ("60", "60 days", False),
    ("", "60 days", False),
])
def test_is_correct(output, gold, expected):
    assert is_correct(output, gold) is expected


def test_aliases_widen_acceptance_without_loosening_it():
    gold = "the December following the financial year end"
    assert is_correct("December", gold, ("December",))
    assert not is_correct("June", gold, ("December",))


def test_accepted_forms_strips_leading_qualifier():
    assert "6 months" in accepted_forms("every 6 months")


def test_kappa_bounds():
    assert cohens_kappa(["a", "b", "a"], ["a", "b", "a"]) == 1.0
    assert cohens_kappa(["a", "a"], ["a", "a"]) == 1.0        # degenerate but total
    assert cohens_kappa(["a"] * 5 + ["b"] * 5, ["a", "b"] * 5) == pytest.approx(0.2)


def test_kappa_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        cohens_kappa(["a"], ["a", "b"])
