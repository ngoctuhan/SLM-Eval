"""Pillar 1 metrics: the outcome table and the rates derived from it.

Every pair produces two independent model calls, one per variant. Joining them on
``pair_id`` places the pair in one cell of a table formed by two binary questions:

* was the model **correct on variant A**?
* did it **abstain on variant B**?

The design spec draws this as a 2x2. It is a 2x3 in practice, because ``hedge`` is a
third behaviour on B and belongs in neither column. Folding hedges into ``abstain``
would inflate DAS for small models — the exact error this pillar exists to expose — so
they get their own column and all six cells sum to 1.

                     correct on A        not correct on A
    abstain on B      DISCRIMINATIVE      BLIND
    answer on B       OVERCONFIDENT       INCOMPETENT
    hedge on B        HEDGED_CAPABLE      HEDGED_INCAPABLE

Rates:

    DAS  = P(discriminative)                     discriminative abstention
    BAR  = P(blind)                              blind abstention
    OCR  = P(overconfident)                      overconfidence
    NAR  = P(abstain on B) = DAS + BAR           the conventional metric
    HR   = P(hedge on B)                         hedge rate, reported separately
    ACC  = P(correct on A)                       task capability
    cDAS = DAS / ACC                             metacognition, capability divided out

NAR is arithmetically the sum of a good cell and a bad one, which is why the metric in
common use cannot separate competence from incapacity.

cDAS is the metric that carries the thesis. The claim is that cDAS degrades faster than
ACC as models shrink; if it does not, the claim is wrong and that is the finding.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from .scoring import Behaviour


class Outcome(str, Enum):
    DISCRIMINATIVE = "discriminative"
    BLIND = "blind"
    OVERCONFIDENT = "overconfident"
    INCOMPETENT = "incompetent"
    HEDGED_CAPABLE = "hedged_capable"
    HEDGED_INCAPABLE = "hedged_incapable"


@dataclass(frozen=True)
class PairResult:
    """One pair, after both variants have been run and scored."""

    pair_id: str
    correct_a: bool
    behaviour_b: Behaviour
    behaviour_a: Behaviour | None = None   # kept for the hedge-on-A sub-analysis
    meta: dict = field(default_factory=dict)

    @property
    def outcome(self) -> Outcome:
        if self.behaviour_b is Behaviour.ABSTAIN:
            return Outcome.DISCRIMINATIVE if self.correct_a else Outcome.BLIND
        if self.behaviour_b is Behaviour.ANSWER:
            return Outcome.OVERCONFIDENT if self.correct_a else Outcome.INCOMPETENT
        return Outcome.HEDGED_CAPABLE if self.correct_a else Outcome.HEDGED_INCAPABLE


@dataclass(frozen=True)
class Interval:
    point: float
    low: float
    high: float

    def __str__(self) -> str:
        return f"{self.point:6.1%} [{self.low:.1%}, {self.high:.1%}]"


@dataclass(frozen=True)
class Metrics:
    n: int
    counts: dict[Outcome, int]
    das: float
    bar: float
    ocr: float
    nar: float
    hedge_rate: float
    accuracy_a: float
    cdas: float

    def as_row(self) -> dict[str, float | int]:
        return {
            "n": self.n, "DAS": self.das, "BAR": self.bar, "OCR": self.ocr,
            "NAR": self.nar, "HR": self.hedge_rate, "ACC_A": self.accuracy_a,
            "cDAS": self.cdas,
        }


def _rate(counts: dict[Outcome, int], *outcomes: Outcome, n: int) -> float:
    return sum(counts.get(o, 0) for o in outcomes) / n if n else 0.0


def compute(results: list[PairResult]) -> Metrics:
    n = len(results)
    if n == 0:
        raise ValueError("no results to score")

    counts: dict[Outcome, int] = {o: 0 for o in Outcome}
    for result in results:
        counts[result.outcome] += 1

    das = _rate(counts, Outcome.DISCRIMINATIVE, n=n)
    bar = _rate(counts, Outcome.BLIND, n=n)
    ocr = _rate(counts, Outcome.OVERCONFIDENT, n=n)
    hedge = _rate(counts, Outcome.HEDGED_CAPABLE, Outcome.HEDGED_INCAPABLE, n=n)
    accuracy = sum(r.correct_a for r in results) / n

    return Metrics(
        n=n, counts=counts, das=das, bar=bar, ocr=ocr, nar=das + bar,
        hedge_rate=hedge, accuracy_a=accuracy,
        # cDAS is undefined when the model gets nothing right on A. Returning 0 would
        # read as "no metacognition" when the truth is "not measurable"; GATE 5 exists
        # to keep accuracy_a above 0.50 so this never fires in a valid run.
        cdas=das / accuracy if accuracy > 0 else float("nan"),
    )


def bootstrap(results: list[PairResult], metric: str, samples: int = 2000,
              alpha: float = 0.05, seed: int = 13) -> Interval:
    """Percentile bootstrap over pairs.

    Resampling is over *pairs*, not over individual model calls: the two variants of a
    pair are not independent observations, and treating them as such would understate
    the interval.
    """
    rng = random.Random(seed)
    point = getattr(compute(results), metric)
    n = len(results)
    draws = []
    for _ in range(samples):
        resample = [results[rng.randrange(n)] for _ in range(n)]
        value = getattr(compute(resample), metric)
        if value == value:                      # skip NaN draws
            draws.append(value)
    if not draws:
        return Interval(point, float("nan"), float("nan"))
    draws.sort()
    low = draws[int((alpha / 2) * (len(draws) - 1))]
    high = draws[int((1 - alpha / 2) * (len(draws) - 1))]
    return Interval(point, low, high)


def gate6_verdict(small: Metrics, large: Metrics,
                  das_gap_min: float = 0.10, nar_gap_max: float = 0.05) -> dict:
    """GATE 6 — the pilot decision gate, evaluated exactly as written down in advance.

    Passing needs **both** conditions. The second one carries the argument: it shows the
    conventional metric cannot see a difference the new metric can. If NAR separates the
    models too, this pillar has rediscovered something already known.
    """
    das_gap = large.das - small.das
    nar_gap = abs(large.nar - small.nar)
    capability_retained = small.accuracy_a / large.accuracy_a if large.accuracy_a else float("nan")
    metacognition_retained = small.cdas / large.cdas if large.cdas else float("nan")
    return {
        "das_gap": das_gap,
        "das_gap_pass": das_gap >= das_gap_min,
        "nar_gap": nar_gap,
        "nar_gap_pass": nar_gap <= nar_gap_max,
        "pass": das_gap >= das_gap_min and nar_gap <= nar_gap_max,
        "capability_retained": capability_retained,
        "metacognition_retained": metacognition_retained,
        # The central claim in one number: metacognition should survive shrinkage worse
        # than capability does.
        "thesis_supported": metacognition_retained < capability_retained,
    }


def format_table(metrics_by_model: dict[str, Metrics]) -> str:
    header = f"{'model':<12}{'n':>5}{'ACC_A':>9}{'NAR':>9}{'DAS':>9}{'BAR':>9}{'OCR':>9}{'HR':>9}{'cDAS':>9}"
    lines = [header, "-" * len(header)]
    for name, m in metrics_by_model.items():
        lines.append(
            f"{name:<12}{m.n:>5}{m.accuracy_a:>8.1%}{m.nar:>9.1%}{m.das:>9.1%}"
            f"{m.bar:>9.1%}{m.ocr:>9.1%}{m.hedge_rate:>9.1%}{m.cdas:>9.1%}"
        )
    return "\n".join(lines)
