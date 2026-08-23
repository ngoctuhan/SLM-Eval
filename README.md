# slm-metacog — Pillar 1: Discriminative Abstention

Benchmarks measure **what a model can do**. This one measures **whether a model knows
what it cannot do** — and how that ability degrades as models shrink.

A high abstention rate has two opposite causes. A model may decline because it
recognised that the document does not contain the answer, or because it could not
process the document at all and declined by default. Every existing abstention
benchmark reports a single rate that sums both. Pillar 1 separates them.

## The paired-twin design

Each item is a **pair**, not a sample. The question is byte-identical across both
variants; only the evidence changes.

```
Question   What is the maximum probation period for management-grade positions?

Variant A  ... The maximum probation period for management-grade positions is
               60 days from the confirmed start date. ...
           -> gold answer: 60 days

Variant B  ... The contractual notice period for management-grade positions is
               45 days from the date of written notice. ...
           -> no answer; the model must abstain
```

Variant B replaces the evidence proposition with a **different field of the same
policy** — same topic, same entity, same specificity, same numeric density. It must be
*close but missing*, never off-topic, or the task collapses into topic detection.

Scoring places each pair in one of four cells:

|                       | correct on A       | not correct on A     |
| --------------------- | ------------------ | -------------------- |
| **abstains on B**     | Discriminative     | Blind abstention     |
| **answers on B**      | Overconfident      | Incompetent          |

```
DAS   = P(correct(A) and abstain(B))     discriminative abstention
BAR   = P(not correct(A) and abstain(B)) blind abstention
OCR   = P(correct(A) and answer(B))      overconfidence
NAR   = P(abstain(B)) = DAS + BAR        the conventional metric
cDAS  = DAS / accuracy(A)                metacognition with capability divided out
```

`NAR` — what the field reports today — is the *sum* of a good cell and a bad one. That
is why it cannot tell competence from incapacity.

## Dataset

150 hand-authored English pairs across 10 enterprise domains. No public dataset was
mined; every document was written for this benchmark, so the corpus carries no
third-party licence and no contamination from question-answering training corpora.

| | |
| --- | --- |
| Pairs | 150 (300 model calls per configuration) |
| Domains | hr_policy, finance_expense, it_service_desk, procurement, legal_compliance, security_access, payroll_benefits, customer_support, facilities_travel, data_governance |
| Per domain | 15 pairs, 15 distinct fictional companies |
| Documents | 150 unique, 6 sentences each, mean 485 characters |
| Evidence position | 50 head / 50 middle / 50 tail (uniform by construction) |
| Licence | CC BY 4.0 (data), MIT (code) |

## Gate status

| Gate | Check | Result |
| --- | --- | --- |
| 2 | A/B invariants, 9 mechanical rules | **PASS** 150/150 on every rule |
| 3 | Shortcut audit, TF-IDF AUC <= 0.60 | **PASS** 0.550 |
| 3 | Shortcut audit, length-only AUC <= 0.55 | **PASS** 0.506 |
| 2 | R4, R6 manual review | **triaged** — 30 priority + 20 control pairs to read |
| 3 | L4 two-annotator blind test | outstanding |
| 4 | Abstention scorer, Cohen kappa >= 0.75 | **tooling built** — needs a model run, then 200 labelled outputs |
| 5 | Sanity check, accuracy(A) >= 0.50 at 4B | tooling built, needs a model |
| 6 | Pilot decision gate | tooling built, needs a model |

Gate 3 is the one that matters. If variant A can be told from variant B by surface
features alone, a model can score well without understanding anything, and every
metric downstream measures the wrong thing. See
[docs/pillar-1.md](docs/pillar-1.md) for what this audit rejected and why.

## Quick start

```bash
make setup      # create .venv and install dependencies
make gates      # build the dataset, then run GATE 2 and GATE 3
make review     # generate the GATE 2 manual review sheet
make dryrun     # run the whole pipeline with no model server, to check plumbing
make test       # 66 tests, including both gates as CI assertions
```

Both validators exit non-zero on failure, so they gate CI directly.

Evaluating real models:

```bash
cp .env.example .env         # then paste your DEEPSEEK_API_KEY
make check                   # one live call per model: keys, endpoint, quirks
make pilot                   # both V4 models, both conditions, then the report
```

Self-hosted and API models take the same path: anything speaking
`POST /v1/chat/completions` works, and the calling code does not distinguish them.

### Model registry

`metacog/config.py` records what each provider actually accepts. "OpenAI-compatible" is
a claim, not a contract, and finding out mid-run costs the run.

| alias | model | notes |
| --- | --- | --- |
| `v4-flash` | `deepseek-v4-flash` | 284B total / 13B active. Thinking disabled. |
| `v4-pro` | `deepseek-v4-pro` | 1.6T total / 49B active. Thinking disabled. |
| `v4-flash-thinking`, `v4-pro-thinking` | same models | Thinking on, for the reasoning-mode comparison. |
| `local` | any | Self-hosted vLLM or llama.cpp. Only path exposing logprobs. |

Two DeepSeek quirks are handled in the registry rather than at call sites:

- **Thinking mode is on by default and ignores `temperature`.** Design spec 7.1 requires
  `temperature=0` for tasks with a gold answer, so the pilot sends
  `thinking: {"type": "disabled"}`. Without it the control is not in force.
- **`seed` and `logprobs` are not documented as supported**, so they are omitted rather
  than risking a 400 partway through a 300-call run.

Thinking on versus off is worth measuring as its own variable later: AbstentionBench
reports that reasoning fine-tuning degrades abstention by 24 percent on average.

## Layout

```
metacog/                 schema, text utilities, scoring, metrics, adapters, registry
data/authoring/en/       source of truth, one JSONL file per domain, human editable
data/p1_paired/en/       compiled release dataset (design spec section 8.1)
data/DATASHEET.md        provenance, construction, intended use, limitations
scripts/build_pairs.py   authoring form -> release form
prompts/p1/              3 templates x 2 abstention-instruction conditions
runners/run_paired.py    runs both variants, writes raw outputs
analysis/report.py       scores raw runs, prints the results table
validation/              GATE 2 invariants + review triage, GATE 3 shortcut audit,
                         GATE 4 kappa tooling
results/gates/           gate outputs as JSON
results/raw/             raw model outputs, one JSONL per run (gitignored)
docs/                    design rationale and the newcomer explainer
tests/                   pytest suite
```

## Authoring a new pair

Edit the domain file under `data/authoring/en/`. A document is a list of sentences and
variant B is one `replacement` string plus the index it overwrites, which makes the
"exactly one sentence differs" invariant true by construction.

Five rules govern the replacement. They are enforced by `validation/invariants.py`, and
they exist because a widely used public dataset fails the shortcut audit for breaking
them (`docs/pillar-1.md`, section 2):

1. **Replace, never delete.** Deletion shortens the context and leaks length.
2. **Stay as specific as the original.** No vague quantifiers — no *some*, *several*,
   *unspecified*, *approximately*. Vagueness is a keyword a model can spot without
   reading the question.
3. **Preserve numeric density.** If the evidence carries a figure, so must the
   replacement.
4. **Same topic, same principal entity.** Off-topic means the task is too easy.
5. **Change exactly one sentence.** Everything else stays byte-identical.

Then run `make gates`. Do not relax a threshold to make a pair pass; the audit numbers
are reported in the paper.

## Documents

- [docs/pillar-1.md](docs/pillar-1.md) — dataset survey, why public sources were
  rejected, gate definitions
- [docs/explainer.md](docs/explainer.md) — the design explained from scratch
- [docs/design-spec-vi.md](docs/design-spec-vi.md) — original three-pillar research
  design (Vietnamese)
