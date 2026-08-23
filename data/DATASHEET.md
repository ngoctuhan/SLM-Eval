# Datasheet — Pillar 1 paired-twin corpus (English, v0.1)

## Motivation

Built to separate two behaviours that existing abstention benchmarks report as one
number: declining because the evidence is genuinely absent, and declining because the
model could not process the document. Answering that question requires minimally
different pairs, which no public dataset provides in a document-grounded enterprise
setting.

## Composition

- 150 pairs. Each pair is one question, one answerable context (A) and one
  unanswerable context (B) differing by exactly one sentence.
- 10 enterprise domains, 15 pairs each: hr_policy, finance_expense, it_service_desk,
  procurement, legal_compliance, security_access, payroll_benefits, customer_support,
  facilities_travel, data_governance.
- 150 unique documents, 6 sentences each, mean 485 characters. No document is reused
  across pairs, so grouped cross-validation by `pair_id` is sound.
- 15 fictional companies, each appearing once per domain.
- Evidence sentence position: 50 head, 50 middle, 50 tail.

## Collection process

Written by hand for this benchmark. Nothing is sampled, translated or paraphrased from
another corpus. Every company, policy, figure and document title is invented.

Variant B is produced by replacing the evidence proposition with a statement about a
**different field of the same policy** — for example a probation period replaced by a
notice period. The replacement is drawn from the same pool of field types that serve as
evidence elsewhere in the domain, so the marginal distribution of sentences is the same
in A and in B. That is what keeps the shortcut audit near chance.

## Preprocessing and validation

Two gates run over the compiled dataset and both are asserted in the test suite.

**GATE 2 — mechanical invariants.** 150/150 on all nine rules: identical question,
equal chunk count, context length within 5 percent, uniform evidence position
(chi-square p = 1.000), gold answer absent from B, exactly one sentence differing, no
vague quantifier in the replacement, digit density preserved within 0.010, replacement
field distinct from evidence field.

**GATE 3 — shortcut audit.** A TF-IDF classifier reading only the context, with the
question hidden and cross-validation grouped by `pair_id`, reaches **AUC 0.550**
against a threshold of 0.60. A length-only baseline reaches **AUC 0.506** against a
threshold of 0.55. Mean context length is 485 characters for A and 486 for B; digit
density is 0.0048 and 0.0049.

Two authoring artefacts were found and removed during construction, both of which
would have invalidated the design:

1. Replacement sentences were systematically longer than the evidence they replaced
   (117 of 150 pairs, mean +7.3 characters). Length-only AUC was 0.552. Sixty-nine
   replacements were shortened; the mean delta is now +0.3 characters.
2. Replacements over-used the `re-` prefix (11 occurrences against 2 in the evidence),
   which the TF-IDF model picked up as a marker token. All eleven were reworded.

## Uses

Intended for evaluating abstention behaviour of language models on document-grounded
enterprise question answering, and specifically for computing DAS, BAR, OCR, NAR and
cDAS as defined in the README.

Not intended for training. The corpus is small by design and the pairing structure
makes it trivially memorisable.

## Distribution

CC BY 4.0. No third-party dataset is embedded, so no upstream licence applies and no
attribution beyond this repository is required.

## Limitations

- English only. A parallel Vietnamese set is planned but not built.
- Single-chunk contexts. Distractor conditions (k in 0, 2, 5, 10) are not yet applied.
- Extractive answers only. Free-form answers would need a judge model for grading.
- Two invariants remain unverified by machine: R4 (same domain and principal entity)
  and R6 (B is close but missing, not off-topic) require human review, as does the
  two-annotator blind test in GATE 3 layer 4.
- Documents are written by a language model under an explicit rule set. They read as
  plausible corporate policy but are not drawn from real internal systems, so any
  claim about contamination resistance rests on the text being original, not on it
  being proprietary.
