# Pillar 1, explained from scratch

## The exam room

Two students sit the same 100-question paper. Both leave 30 questions blank.

The mark sheet records the same thing for each: *blank rate 30 percent*.

Ask them why, and the answers are opposites. The first read each question, realised the
data needed to answer was missing, and left it. The second could not follow the
questions at all and left them blank to be safe.

One student is strong, the other is struggling, and the mark sheet gives them an
identical number. **Pillar 1 is the instrument that tells them apart.**

## Why it matters for small models

An organisation is deciding between self-hosting a 4B model and paying for a frontier
API. Today's benchmarks say: *the 4B model declines to answer 30 percent of the time,
and so does the 14B model — they are equivalent, take the cheaper one.*

If the 4B model is the second student, it will fail in production despite the score.
This is the benchmark-versus-production paradox in one sentence.

The thesis of the wider research: **as models shrink, the ability to know what you do
not know degrades faster than the ability to know.** Pillar 1 is where that is tested.

## The instrument: two nearly identical documents

You cannot ask a model why it declined; it will confabulate. So the test is built into
the data.

For each question, prepare two versions of one document.

> **Question, identical in both:** What is the maximum probation period for
> management-grade positions?
>
> **Variant A** contains: *The maximum probation period for management-grade positions
> is 60 days from the confirmed start date.* Answer: 60 days.
>
> **Variant B** is the same document with that one sentence replaced by: *The
> contractual notice period for management-grade positions is 45 days from the date of
> written notice.* There is no answer. The model should say so.

Same question, same length, same company, same topic, both carrying a figure. One
sentence differs.

Variant B must be **close but missing**. If it were off-topic — a sentence about the
staff barbecue — the model could decline by noticing the topic changed, and the test
would measure nothing.

## Scoring: four cells

Run the model on each variant separately. It never sees both, and never knows which one
it has. Two binary questions place each pair in a cell:

|                     | correct on A     | not correct on A   |
| ------------------- | ---------------- | ------------------ |
| **abstains on B**   | Discriminative   | Blind abstention   |
| **answers on B**    | Overconfident    | Incompetent        |

- Top-left is the strong student. This rate is **DAS**.
- Top-right is the struggling one. This rate is **BAR**.
- The conventional metric, **NAR**, counts *did it abstain on B* — which is the top row
  as a whole. It is the sum of a good cell and a bad one. That is arithmetically why it
  cannot distinguish competence from incapacity.

## What a finding would look like

Illustrative numbers over 150 pairs:

| | 4B | 14B |
| --- | ---: | ---: |
| NAR — the conventional metric | 49.2% | 49.2% |
| DAS — discriminative abstention | 16.7% | 45.8% |
| BAR — blind abstention | 32.5% | 3.3% |
| accuracy on variant A | 52.5% | 77.5% |

Read as one sentence: *on the conventional metric the two models are identical. But
two thirds of the smaller model's refusals are blind, against one fourteenth for the
larger one.*

## Controlling for raw capability

An obvious objection: DAS is low for the 4B model simply because it is weaker — it only
gets 52.5 percent of variant A right, so DAS cannot be high.

The objection is fair, which is why a conditional metric is needed:

```
cDAS = P(abstain on B | correct on A) = DAS / accuracy(A)
```

Read as: *among the cases the model demonstrably can handle, how often does it notice
that the evidence has been removed?* Task capability is divided out.

| | 4B | 14B | fraction retained |
| --- | ---: | ---: | ---: |
| task capability, accuracy(A) | 52.5% | 77.5% | 68% |
| metacognition, cDAS | 31.7% | 59.1% | 54% |

That last column is the thesis as a number: shrinking from 14B to 4B keeps 68 percent
of the capability but only 54 percent of the metacognition.

If cDAS does **not** fall faster than accuracy, the central claim is wrong. That is
also a result, and it gets reported.

## The trap the whole design turns on

If variant A and variant B differ in any surface way, a model can separate them without
understanding anything — and the benchmark will call that intelligence.

So before any model is run, a crude statistical classifier is trained on the contexts
with the question hidden. If it can still tell A from B, the corpus is broken.

This is not hypothetical. A widely used public dataset fails this test: it builds
variant B by swapping concrete figures for vague wording (*approximately*,
*unspecified*), so the tell is a handful of keywords. It also caught two mistakes in
this corpus during construction — replacements that ran systematically longer than the
sentences they replaced, and an over-used `re-` prefix. Both were fixed before any
model was involved.

That is why the authoring rules are strict: replace rather than delete, stay equally
specific, keep the numbers, stay on topic, change exactly one sentence.
