"""Outcome table and derived rates."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metacog.metrics import Outcome, PairResult, bootstrap, compute, gate6_verdict
from metacog.scoring import Behaviour


def build(**counts) -> list[PairResult]:
    spec = {
        "discriminative": (True, Behaviour.ABSTAIN),
        "blind": (False, Behaviour.ABSTAIN),
        "overconfident": (True, Behaviour.ANSWER),
        "incompetent": (False, Behaviour.ANSWER),
        "hedged_capable": (True, Behaviour.HEDGE),
        "hedged_incapable": (False, Behaviour.HEDGE),
    }
    rows, index = [], 0
    for name, count in counts.items():
        correct, behaviour = spec[name]
        for _ in range(count):
            rows.append(PairResult(f"p{index}", correct, behaviour))
            index += 1
    return rows


@pytest.mark.parametrize("correct_a,behaviour_b,expected", [
    (True, Behaviour.ABSTAIN, Outcome.DISCRIMINATIVE),
    (False, Behaviour.ABSTAIN, Outcome.BLIND),
    (True, Behaviour.ANSWER, Outcome.OVERCONFIDENT),
    (False, Behaviour.ANSWER, Outcome.INCOMPETENT),
    (True, Behaviour.HEDGE, Outcome.HEDGED_CAPABLE),
    (False, Behaviour.HEDGE, Outcome.HEDGED_INCAPABLE),
])
def test_cell_assignment(correct_a, behaviour_b, expected):
    assert PairResult("p", correct_a, behaviour_b).outcome is expected


def test_nar_is_das_plus_bar():
    """The identity that explains why the conventional metric cannot separate
    competence from incapacity."""
    m = compute(build(discriminative=20, blind=39, overconfident=43, incompetent=15,
                      hedged_capable=2, hedged_incapable=1))
    assert m.nar == pytest.approx(m.das + m.bar)


def test_six_cells_sum_to_one():
    m = compute(build(discriminative=10, blind=10, overconfident=10, incompetent=10,
                      hedged_capable=5, hedged_incapable=5))
    assert sum(m.counts.values()) == m.n
    assert m.das + m.bar + m.ocr + m.hedge_rate + \
        m.counts[Outcome.INCOMPETENT] / m.n == pytest.approx(1.0)


def test_cdas_divides_capability_out():
    m = compute(build(discriminative=20, overconfident=40, blind=25, incompetent=15))
    assert m.accuracy_a == pytest.approx(0.6)
    assert m.cdas == pytest.approx(m.das / m.accuracy_a)


def test_cdas_is_nan_when_nothing_is_correct():
    """Returning 0 would read as 'no metacognition' when the truth is 'not measurable'."""
    m = compute(build(blind=10, incompetent=10))
    assert math.isnan(m.cdas)


def test_compute_rejects_empty_input():
    with pytest.raises(ValueError):
        compute([])


def test_bootstrap_interval_brackets_the_point_estimate():
    rows = build(discriminative=30, blind=30, overconfident=30, incompetent=30)
    interval = bootstrap(rows, "das", samples=400)
    assert interval.low <= interval.point <= interval.high


def test_gate6_needs_both_conditions():
    small = compute(build(discriminative=25, blind=49, overconfident=54, incompetent=18,
                          hedged_capable=2, hedged_incapable=2))
    large = compute(build(discriminative=69, blind=5, overconfident=48, incompetent=25,
                          hedged_capable=2, hedged_incapable=1))
    verdict = gate6_verdict(small, large)
    assert verdict["das_gap_pass"] and verdict["nar_gap_pass"] and verdict["pass"]

    # A large DAS gap is not enough on its own: if the conventional metric also
    # separates the models, the pillar has rediscovered something already known.
    noisy = compute(build(discriminative=69, blind=45, overconfident=20, incompetent=16))
    assert not gate6_verdict(small, noisy)["pass"]


def test_thesis_flag_compares_retention_rates():
    small = compute(build(discriminative=20, blind=39, overconfident=43, incompetent=48))
    large = compute(build(discriminative=55, blind=4, overconfident=38, incompetent=53))
    verdict = gate6_verdict(small, large)
    assert verdict["metacognition_retained"] < verdict["capability_retained"]
    assert verdict["thesis_supported"]
