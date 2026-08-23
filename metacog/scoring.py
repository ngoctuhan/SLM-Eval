"""GATE 4 — scoring model outputs.

Two independent labels come out of every model response:

* **behaviour** — one of ``answer`` / ``abstain`` / ``hedge``
* **correctness** — only meaningful on variant A, which is the variant that has a gold
  answer

``hedge`` is a class of its own and is never folded into ``abstain``. Folding it in
inflates DAS for small models, which is precisely the error Pillar 1 exists to expose,
and the hedge rate by model size is a finding worth reporting on its own.

The behaviour scorer runs in three tiers, per design spec section 2.5:

    tier 1  exact match against the refusal string the prompt demands
    tier 2  a classifier over the remaining outputs
    tier 3  human cross-check on 200 samples, reporting Cohen's kappa

Tier 2 ships here as a lexical baseline, not a trained model. A trained encoder needs
300 hand-labelled outputs that do not exist until a model has been run, so the baseline
exists to bootstrap that labelling round and to be the thing the trained classifier has
to beat. ``BehaviourScorer`` takes an optional ``classifier`` so a trained model drops
in without touching call sites. **The kappa gate applies to whichever tier 2 is in use:
no metric is trustworthy until kappa reaches 0.75.**
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

REFUSAL_STRING = "NO INFORMATION"
KAPPA_THRESHOLD = 0.75


class Behaviour(str, Enum):
    ANSWER = "answer"
    ABSTAIN = "abstain"
    HEDGE = "hedge"


# Unambiguous refusals. Matching any of these with nothing substantive alongside is
# an abstention.
ABSTAIN_PATTERNS = [
    r"\bno information\b",
    r"\bnot (?:stated|specified|mentioned|provided|given|included|present|available)\b",
    r"\b(?:does|do|did) not (?:state|specify|mention|contain|provide|say|include)\b",
    r"\bcannot be (?:determined|answered|established|found)\b",
    r"\b(?:i|we) (?:cannot|can't|am unable to|are unable to) (?:answer|determine|find)\b",
    r"\bthe (?:document|context|passage|text|policy) does not\b",
    r"\bthere is no (?:information|mention|statement|reference)\b",
    r"\binsufficient information\b",
    r"\bunanswerable\b",
]

# Half-commitment. The model neither refuses nor commits to a value.
HEDGE_PATTERNS = [
    r"\b(?:might|may|could|possibly|presumably|likely|probably|appears to|seems to)\b",
    r"\bit is (?:unclear|ambiguous|not clear)\b",
    r"\bwithout further\b",
    r"\bi am not (?:certain|sure)\b",
    r"\bif .{0,40}\bthen\b",
    r"\bhowever\b.{0,80}\bnot\b",
    r"\bbut .{0,40}\bnot (?:explicit|clear|stated)\b",
]

# A concrete quantity. Its presence is what separates a real answer from a hedge.
QUANTITY = re.compile(
    r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b", re.I
)


class Classifier(Protocol):
    """Drop-in replacement for the tier 2 baseline."""

    def __call__(self, text: str) -> Behaviour: ...


@dataclass(frozen=True)
class BehaviourLabel:
    behaviour: Behaviour
    tier: int          # which tier decided it — report the tier mix alongside results
    evidence: str      # the pattern or string that fired, for auditing


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").strip()
    text = re.sub(r"[*_`#>]+", " ", text)          # markdown emphasis
    return re.sub(r"\s+", " ", text)


class BehaviourScorer:
    """Assigns one of answer / abstain / hedge to a raw model output."""

    def __init__(self, classifier: Classifier | None = None,
                 refusal_string: str = REFUSAL_STRING) -> None:
        self.classifier = classifier
        self.refusal_string = refusal_string

    def __call__(self, output: str) -> BehaviourLabel:
        text = normalise(output)
        if not text:
            # An empty output is a failure to respond, not a considered refusal.
            return BehaviourLabel(Behaviour.HEDGE, 1, "empty output")

        # Tier 1 — the prompt demanded a fixed string and the model produced exactly it.
        stripped = text.rstrip(".!").strip()
        if stripped.upper() == self.refusal_string.upper():
            return BehaviourLabel(Behaviour.ABSTAIN, 1, "exact refusal string")

        # Tier 2 — trained classifier if one was supplied, otherwise the lexical baseline.
        if self.classifier is not None:
            return BehaviourLabel(self.classifier(text), 2, "classifier")
        return self._lexical(text)

    def _lexical(self, text: str) -> BehaviourLabel:
        lowered = text.lower()
        abstain_hit = next((p for p in ABSTAIN_PATTERNS if re.search(p, lowered)), None)
        hedge_hit = next((p for p in HEDGE_PATTERNS if re.search(p, lowered)), None)
        has_quantity = bool(QUANTITY.search(text))

        if abstain_hit and not has_quantity:
            return BehaviourLabel(Behaviour.ABSTAIN, 2, abstain_hit)
        if abstain_hit and has_quantity:
            # "The document does not state a probation period, but it mentions 45 days."
            # Refuses and supplies a figure at once — that is a hedge, not a refusal.
            return BehaviourLabel(Behaviour.HEDGE, 2, f"{abstain_hit} + quantity")
        if hedge_hit:
            return BehaviourLabel(Behaviour.HEDGE, 2, hedge_hit)
        if not has_quantity and len(lowered.split()) > 25:
            # Long, no refusal marker, no figure: discursive non-commitment.
            return BehaviourLabel(Behaviour.HEDGE, 2, "verbose, no quantity")
        return BehaviourLabel(Behaviour.ANSWER, 2, "no refusal or hedge marker")


# --------------------------------------------------------------------------- correctness

_ARTICLES = re.compile(r"\b(?:a|an|the|of|per|at|in|on|to|for|from)\b")
_PUNCT = re.compile(r"[^\w\s%.:]")
# Keep "." and ":" only between digits, so 2.5 and 06:00 survive but "days." does not.
_TRAILING_DOT = re.compile(r"(?<!\d)[.:]|[.:](?!\d)")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")

# A model may answer "every six months" where the gold says "every 6 months". Grading
# that wrong depresses accuracy(A), and DAS is bounded by accuracy(A), so a lenient
# reading here protects the headline metric from a formatting artefact.
_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11",
    "twelve": "12", "fifteen": "15", "twenty": "20", "thirty": "30", "forty": "40",
    "fifty": "50", "sixty": "60", "ninety": "90",
}

# Gold answers often carry a leading qualifier that a correct answer may omit:
# "every 6 months" answered as "6 months", "longer than 7 hours" as "7 hours".
_QUALIFIER_PREFIX = re.compile(
    r"^(?:every|at least|at most|up to|more than|less than|fewer than|longer than|"
    r"shorter than|smaller than|larger than|greater than|above|below|within|after|"
    r"before|no later than)\s+"
)


def normalise_answer(text: str) -> str:
    text = normalise(text).lower()
    text = _PUNCT.sub(" ", text)
    text = _TRAILING_DOT.sub(" ", text)
    text = _ARTICLES.sub(" ", text)
    text = " ".join(_NUMBER_WORDS.get(w, w) for w in text.split())
    return re.sub(r"\s+", " ", text).strip()


def _numbers(text: str) -> list[str]:
    return [n.replace(",", "") for n in _NUMBER.findall(text)]


def _matches(normalised_output: str, gold: str) -> bool:
    normalised_gold = normalise_answer(gold)
    if not normalised_gold:
        return False
    gold_numbers = _numbers(normalised_gold)
    if gold_numbers:
        output_numbers = set(_numbers(normalised_output))
        if not set(gold_numbers).issubset(output_numbers):
            return False
        # Numbers match; the unit or qualifier must survive too, otherwise "60" alone
        # would satisfy a gold of "60 days".
        gold_words = [w for w in normalised_gold.split() if not _NUMBER.fullmatch(w)]
        return all(w in normalised_output.split() for w in gold_words)
    return normalised_gold in normalised_output


def accepted_forms(gold: str, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Every phrasing that counts as correct: the gold, its qualifier-stripped core,
    and any alias the item declares."""
    forms = [gold, *aliases]
    stripped = _QUALIFIER_PREFIX.sub("", normalise_answer(gold))
    if stripped and stripped != normalise_answer(gold):
        forms.append(stripped)
    return tuple(dict.fromkeys(f for f in forms if f))


def is_correct(output: str, gold: str, aliases: tuple[str, ...] = ()) -> bool:
    """Grade a variant A answer.

    Gold answers in this corpus are short quantities, durations or dates, so containment
    after normalisation is a fair test — but containment alone would accept "45 days"
    for a gold of "5 days", so every number in the gold must appear as a whole token.

    An answer counts if it matches the gold, the gold with a leading qualifier removed,
    or any alias declared on the item.
    """
    if not output or not gold:
        return False
    normalised_output = normalise_answer(output)
    return any(_matches(normalised_output, form) for form in accepted_forms(gold, aliases))


# --------------------------------------------------------------------------- tier 3

def cohens_kappa(a: list[str], b: list[str]) -> float:
    """Chance-corrected agreement between two labellers over the same items."""
    if len(a) != len(b):
        raise ValueError("label lists must be the same length")
    if not a:
        raise ValueError("no labels to compare")
    labels = sorted(set(a) | set(b))
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((a.count(k) / n) * (b.count(k) / n) for k in labels)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def confusion(a: list[str], b: list[str]) -> dict[tuple[str, str], int]:
    matrix: dict[tuple[str, str], int] = {}
    for x, y in zip(a, b):
        matrix[(x, y)] = matrix.get((x, y), 0) + 1
    return matrix
