# Pillar 1 — Discriminative Abstention: sources, decisions, gates

Companion to the three-pillar research design in
[design-spec-vi.md](design-spec-vi.md) (Vietnamese).

---

## 1. Two kinds of pairing, and why they are not interchangeable

Every dataset with answerable and unanswerable items pairs them one of two ways, and
the two are mirror images.

| Pairing | Held fixed | Varied | Controls for | Examples |
| --- | --- | --- | --- | --- |
| **Question-anchored** | the question | the context | question difficulty | SUM, TreeCut, MuSiQue-Full, FaithEval |
| **Context-anchored** | the context | the question | context difficulty and noise | SQuAD 2.0, UIT-ViQuAD 2.0 |

This benchmark is question-anchored: the same question is asked of both variants, so a
difference in behaviour cannot be explained by one question being harder than another.

Context-anchored corpora cannot be used directly. In UIT-ViQuAD 2.0, verified on the
data, the number of questions shared between the answerable and unanswerable classes is
**0 of 3,814** — the questions are always different by construction.

## 2. Why no public dataset was used

Public sources were surveyed and audited before being rejected. The audits were run,
not read off papers.

### SUM (Synthetic Unanswerable Math) — fails the shortcut audit

`lime-nlp/Synthetic_Unanswerable_Math`, 36,480 explicitly paired items. Question-
anchored, downloadable, apparently ideal.

| Subset | Pairs | TF-IDF AUC |
| --- | ---: | ---: |
| All pairs | 36,480 | **0.805** |
| Filtered: identical final question sentence | 7,997 | **0.729** |
| Filtered further: length within 5 percent | 2,503 | **0.673** |

The threshold is 0.60. Filtering on every invariant this design requires still leaves
0.673. The leak is not length — a length-only baseline sits at 0.505 — it is
vocabulary. SUM builds its unanswerable variant by replacing concrete figures with
vague quantifiers, so the highest-weighted tokens toward the unanswerable class are
`some, unspecified, several, certain, an unspecified number of`, and digit density
drops from 3.50 percent to 2.67 percent. A model can abstain by spotting hedging
language without ever reading the question. The leak is structural; filtering cannot
remove it.

This failure is the origin of the five authoring rules in the README.

### Others

| Source | Pairing | Why not used |
| --- | --- | --- |
| TreeCut | question-anchored | Same mechanism as SUM. Removes a premise, so B is shorter and fails the length invariant. Synthetic mathematics, not documents. |
| MuSiQue-Full | question-anchored | Closest public match and CC BY 4.0, but already a component of AbstentionBench. Kept as a fallback. |
| FaithEval | question-anchored | Uses the correct replacement strategy; general-domain rather than enterprise. |
| AbstentionBench | none | CC-BY-NC-4.0, non-commercial. Useful as a NAR reference point, not as source material. |
| RGB | none | Source of the noise taxonomy for the distractor conditions. |
| Magic Mushroom | none | Distractor generator for k in 0, 2, 5, 10. |
| SQuAD 2.0, UIT-ViQuAD 2.0 | context-anchored | Wrong pairing. UIT-ViQuAD 2.0 is clean — a question-only classifier reaches AUC 0.507 — but its licence is unconfirmed on HuggingFace and the original corpus requires a signed user agreement. |

Writing the corpus from scratch removes the licence question entirely and eliminates
contamination from question-answering training data.

## 3. Prior work this pillar must answer to

**Two Axes of LLM Abstention: Answer Correctness and Question Answerability**
(arXiv 2607.08456) separates answerability from correctness across Gemma 2 2B, Qwen 2.5
3B/7B/14B and Llama 3.1 8B — the exact size range planned here. It must be cited.

What remains distinct: that work draws answerable and unanswerable items from separate
benchmarks (SelfAware, CREPE), so the two classes differ in vocabulary and topic as
well as in answerability. It compares model outputs against hidden states rather than
decomposing behaviour by model size. The minimally-different pairing, and the BAR and
cDAS decomposition it makes possible, are not covered.

AbstentionBench already includes MuSiQue and SQuAD 2.0. Any overlap must be stated
explicitly: the contribution is the paired design and the metric decomposition, not a
new source of questions.

## 4. The gates

Each gate has a rule, a test, a threshold and a defined action on failure. Do not pass
a gate that has not been met, and do not relax a threshold — these numbers are reported.

### GATE 0 — pairing definition (settled)

Question-anchored. Variant B replaces the evidence proposition with a different field
of the same policy. A context-anchored baseline may be run alongside for comparison.

### GATE 1 — material (met)

150 pairs authored across 10 domains, 15 fictional companies, no external dependency.

### GATE 2 — mechanical invariants (met)

Nine rules, all machine-checked by `validation/invariants.py`, currently 150/150 on
each. R3 permits a 5 percent failure rate; every other rule is absolute. Two rules
remain manual: R4 (same domain and principal entity) and R6 (B is close but missing).

### GATE 3 — shortcut audit (met, machine layers)

Four layers. Layers 1 to 3 are automated by `validation/shortcut_audit.py`; layer 4 is
a two-annotator blind test that has not yet been run.

Cross-validation must be grouped by `pair_id`. Without grouping, the A and B halves of
one pair land in both train and test and the AUC is inflated past the point of meaning.

Current: TF-IDF AUC 0.550 (threshold 0.60), length-only AUC 0.506 (threshold 0.55).

### GATE 4 — abstention scorer (not started)

Three classes, `abstain` / `answer` / `hedge`, scored in three tiers: exact match on
the required output string, a small fine-tuned classifier over 300 hand-labelled
outputs, and a 200-sample human cross-check reporting Cohen kappa against the
classifier. **Kappa must reach 0.75 before any metric is trusted**, because every
downstream number is a function of this scorer.

`hedge` is not folded into `abstain`. Folding it in would inflate DAS for small models,
which is precisely the error this pillar exists to expose. Recommended treatment: a
2x3 table whose six cells sum to 1, with the hedge rate by model size reported as a
finding in its own right.

### GATE 5 — capability sanity check (not started)

The four-cell table is only meaningful if the model can actually do variant A.
Threshold: accuracy on A of at least 0.50 for the smallest model. Below that, DAS
floors at zero for a trivial reason and the corpus needs to be made easier.

### GATE 6 — pilot decision gate (not started)

Record the criteria before running and honour them.

Pass requires **both**: `DAS(14B) - DAS(4B) >= 10 points` **and**
`|NAR(14B) - NAR(4B)| <= 5 points`.

The second condition carries the argument. It demonstrates that the conventional metric
cannot see a difference the new metric can. If NAR separates the models too, this
pillar has rediscovered something already known.

Also report `cDAS = DAS / accuracy(A)`. The central claim is that cDAS falls faster
than accuracy(A) as models shrink. If it does not, the claim is wrong, and that is a
result worth reporting.

### GATE 7 — controlled variables (after Gate 6)

Distractor count k in 0, 2, 5, 10 drawn from the Magic Mushroom taxonomy and inserted
into both A and B so the invariants hold; neutral versus explicit abstention
instruction; three prompts and three seeds; then the parallel Vietnamese set and the
language shift measurement.
