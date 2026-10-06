# Structured Decision Architecture

This is the shared source of truth for internal task routing and decision state across all six SWT Skills. It describes the minimum decision record needed to choose a safe, useful next action. It is not a transcript, explanation of hidden reasoning, or a user-facing form.

## Operating rules

1. Decide the user-facing task from the current request and known context; do not route from keywords alone.
2. Check immediate danger and material fact conflicts before ordinary routing.
3. Reuse confirmed facts. Ask only for missing information that changes the route, safety, or next action.
4. Keep the decision record optional and minimal. Never expose it as a JSON dump.
5. Do not store hidden chain of thought, speculative personality judgments, or unnecessary personal data.
6. A decision record may support an answer, a clarification, a calculation, a specialist handoff, or a pause. It does not replace the six-Skill boundaries.

## Canonical finite values

### Intent

Use one of the task types defined by `routing-policy.md`:

`NAVIGATION | DOCUMENT_CHECK | DECISION | INTERVIEW | ENGLISH_PRACTICE | GENERAL_ENGLISH | ENGLISH_ASSESSMENT | FORM_FILLING | CONFLICT | CALCULATION | EMERGENCY | GENERAL_QA`

### Skill route

`swt | swt-application | swt-position | swt-english | swt-visa | swt-arrival`

An optional supporting route may be added when a single request genuinely needs a second specialist. Do not create Skills or route aliases here.

The validator checks that obvious single-owner intents stay on their owning route: navigation and general SWT questions to `swt`; calculation to `swt-position`; Interview, English Practice, General English and English Assessment to `swt-english`; form filling to application, visa or arrival. Document checks and conflicts remain object-dependent and may use any existing Skill.

### Stage

Use the existing stage model only: `00` through `11`. Stage is optional when irrelevant or unknown; do not infer a new stage.

### Confidence

`high | medium | low`

Confidence describes confidence in the route or current conclusion, not a numeric probability of program, visa, or job success.

### Risk

`green | yellow | red | emergency`

These values retain the existing risk policy. A red risk or emergency can require pausing a specific action while safe, reversible assistance continues.

### Evidence status

`confirmed | conditional | pending_verification | conflicting | historical`

These values map directly to `evidence-policy.md`. Never convert a pending or conflicting fact into a confirmed fact to make a route easier.

### Materiality

`non_material | material | critical`

- `non_material`: does not change the current answer or action.
- `material`: changes part of the conclusion or which evidence is needed.
- `critical`: changes identity, eligibility, safety, legal status, or an irreversible action.

### Next action

`answer | ask_one_question | calculate | load_known_context | route_specialist | verify_fact | pause_action | start_assessment | start_practice | start_interview | finish`

## Optional Decision Record

The following fields are an internal working shape, not a requirement to persist every turn:

```yaml
decision:
  intent: GENERAL_QA
  route: swt
  supporting_route: null
  stage: null
  confidence: medium
  risk: green
  evidence_status: confirmed
  materiality: non_material
  missing_information: none
  clarification_level: null
  known_context_keys: []
  missing_information_keys: []
  next_action: answer
  reason_code: direct_answer
```

`reason_code` is a short label from a finite, implementation-owned set; it must not contain prose reasoning. The reference validator currently accepts `direct_answer`, `context_needed`, `route_by_object`, `risk_pause`, `fact_conflict`, `calculation_needed`, `assessment_requested`, `practice_requested`, `roleplay_requested`, `stage_unknown`, and `other`.

## Missing information and clarification mapping

The optional decision field `missing_information` uses `none | low_impact | conclusion_changes | safety_blocking`. Map it to the existing interaction protocol without replacing that protocol:

| Decision model | Existing clarification protocol | Action |
|---|---|---|
| `none` | Level 1 | Answer without asking. |
| `low_impact` | Level 2 | Give the useful part and ask only if needed. |
| `conclusion_changes` | Level 3 | Ask the single most important question. |
| `safety_blocking` | Level 4 | Pause the affected high-risk action and verify. |

When multiple fields are missing, record the highest-impact class and ask no more than the interaction protocol allows. `missing_information_keys` must not repeat any `known_context_keys`. Do not ask again for information already present in current conversation or loaded, authorized user data.

## Invariants

- The route must be one of the six Skills and the task must remain within that Skill's documented responsibility.
- A critical, conflicting fact affecting an irreversible action requires `verify_fact` or `pause_action` before that action.
- Visa communication practice may improve clarity only after `swt-visa` facts are confirmed; fact conflict pauses language optimization.
- For `swt-english`, ASSESS and PRACTICE remain separate. Practice observations never overwrite a formal Assessment Result.
- No decision record may contain chain of thought, credentials, full identifiers, full document images, or raw conversation transcripts.
- Do not convert confidence into a guarantee or an external success probability.
