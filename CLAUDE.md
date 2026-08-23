# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

`slm-metacog` measures whether a language model **knows when it cannot answer**, and how
that ability degrades as models shrink. Current scope is **Pillar 1 — Discriminative
Abstention**.

The thesis: as models shrink, metacognition degrades faster than capability. If true, it
explains why small models score well on benchmarks and fail in production.

The instrument: every item is a **pair**. Variant A is a document containing the answer.
Variant B is the same document with the evidence sentence **replaced** by a different
fact of the same kind. The question is byte-identical across both. A capable model
answers A and refuses B. An incapable one refuses both — and the conventional metric
scores those two models the same.

The corpus is 150 hand-authored English enterprise-policy pairs across 10 domains. It is
authored, not mined: no public dataset survived the shortcut audit, and the licensing is
cleaner this way. See `docs/pillar-1.md` §2.

## Read first

| When | Read |
| --- | --- |
| Starting any session | this file, then `README.md` |
| You need the *why* behind a decision | `docs/pillar-1.md` — sources, rejected datasets, gate definitions |
| You need to explain the project to someone | `docs/explainer.md` |
| You are touching the dataset | `data/DATASHEET.md`, then the B-variant contract below |
| You need the original research design | `docs/design-spec-vi.md` (Vietnamese, the authoritative spec) |

`docs/design-spec-vi.md` and `docs/pillar1-survey-and-gates-vi.md` are Vietnamese. The
user works in Vietnamese; **the repository is English** — code, comments, docs, commits,
dataset. Keep that split.

## Commands

```bash
make setup    # .venv + dependencies
make gates    # build the dataset, run GATE 2 and GATE 3
make review   # GATE 2 manual review sheet (30 priority + 20 control pairs)
make dryrun   # full pipeline, no model server, no key — checks plumbing
make check    # one live call per model — keys, endpoint, provider quirks
make pilot    # both DeepSeek V4 models, both conditions, then the report
make test     # the test suite
```

Validators exit non-zero on failure, so they gate CI directly.

## Gate status

| Gate | State |
| --- | --- |
| 0 pairing definition | settled — Q-anchored, author variant B |
| 1 material | met — 150 pairs, 10 domains |
| 2 mechanical invariants | **PASS**, 150/150 on every rule |
| 2 manual review (R4, R6) | **in progress — the user is reading the review sheet** |
| 3 shortcut audit | **PASS** — TF-IDF AUC 0.550, length-only 0.506 |
| 4 abstention scorer | tooling built; needs a model run, then 200 labelled outputs |
| 5 capability sanity check | tooling built; needs a model |
| 6 pilot decision gate | tooling built; needs a model |

Blocked on the user pasting `DEEPSEEK_API_KEY` into `.env`.

## Principles

These are load-bearing. Several were learned by getting them wrong first.

### Gates

1. **Never loosen a threshold to make a gate pass.** The numbers go in a paper. If a gate
   fails, fix the data. GATE 3's AUC ≤ 0.60 in particular is the whole validity argument.
2. **Rewriting one pair invalidates both gates.** After any edit to
   `data/authoring/`, run `make gates` and record the new figures. A rewrite moves GATE 3.
3. **Record what was skipped.** Sampling, truncation and unreviewed pairs must appear in
   the output. A silent cap reads as full coverage.

### The B-variant contract

Breaking any of these makes the pair measure the wrong thing. `validation/invariants.py`
enforces the mechanical ones; the rest need judgement.

1. **Replace, never delete.** Deleting shortens the context and leaks the answer's absence.
2. **The replacement must be as specific as the evidence.** No vague quantifiers — `some`,
   `unspecified`, `approximately`, `to be determined`. This is exactly what makes the
   public SUM dataset leak: it swaps concrete figures for vague ones, and a bag-of-words
   classifier separates its variants at AUC 0.673 without reading the question.
3. **Preserve digit density.** If the evidence carries a figure, so must the replacement.
4. **Same topic, same principal entity.** An off-topic B turns the task into topic
   detection, which is trivial.
5. **Change exactly one sentence.** Everything else byte-identical.

### Measurement

6. **`hedge` is never folded into `abstain`.** A model that refuses *and* supplies a figure
   has hedged. Counting that as abstention inflates DAS for small models — the precise
   error this pillar exists to expose. The outcome table is 2×3, six cells summing to 1.
7. **`cDAS = DAS / accuracy(A)` carries the thesis.** Raw DAS is bounded by capability, so
   a low DAS at 4B could just mean "4B is weak". cDAS divides capability out.
8. **The shortcut audit must group cross-validation folds by `pair_id`.** Otherwise the two
   halves of one pair land in both train and test and the AUC is meaningless.
9. **Never let the scorer see `reasoning_content`.** A chain of thought saying "the document
   does not state this" alongside an answer that commits to a figure is an **answer**.
10. **GATE 6 needs both conditions.** A large DAS gap alone is not the finding. The second
    condition — that NAR, the conventional metric, does *not* separate the models — is what
    makes the result worth publishing.

### Engineering

11. **Always persist raw model output**, never only the label. The error taxonomy planned
    for later depends on it and re-running the matrix to recover it is expensive.
12. **`data/authoring/` is the source of truth.** `data/p1_paired/` is built by
    `scripts/build_pairs.py`. Never hand-edit the built file.
13. **Provider quirks live in `metacog/config.py`**, not in call sites. "OpenAI-compatible"
    is a claim, not a contract. DeepSeek V4 enables thinking by default and thinking mode
    **silently ignores `temperature`** — the spec requires `temperature=0`, so the registry
    sends `thinking: {"type": "disabled"}`. It is also undocumented for `seed` and
    `logprobs`, which are therefore omitted rather than risked mid-run.
14. **One OpenAI-compatible interface for every model.** Self-hosted and API models take the
    same path. Anything that does not speak the protocol needs a shim, not a second code
    path.
15. **Verify against a real HTTP round trip**, not only in-process fakes. The
    `from_spec(base_url=…)` crash only surfaced against a live socket.
16. **Zero third-party runtime dependencies** beyond `pyarrow`/`pandas`/`scikit-learn` for
    validation. `.env` parsing and HTTP are hand-rolled and should stay that way.

### Scope

17. **Do not mine public QA datasets for pairs.** Settled decision. SQuAD 2.0 and
    UIT-ViQuAD 2.0 are *context-anchored* (same context, different question) and do not fit
    the design; SUM and TreeCut leak. See `docs/pillar-1.md` §1–2.
18. **Vietnamese is an experimental variable, not the claim.** The VI corpus comes after the
    EN one clears every gate, and must use the identical authoring procedure — otherwise
    the EN/VI comparison confounds language with design.

## Conventions

- Python 3.12, type hints, dataclasses. Comments explain *why*, not *what*.
- Every validator: prints a human-readable report, writes JSON to `results/gates/`, exits
  non-zero on failure.
- New rules get a test. `tests/test_adapters.py` shows the pattern for regressions.
- Never commit `.env`, `results/raw/`, or `.venv/`.

## Git

- **Short commit messages.** One line, imperative, lower case. No body unless it earns one.
- **No `Co-Authored-By` trailer and no tool attribution.** The user has asked for this
  explicitly.
- Commit when asked. Branch before committing if on the default branch.
