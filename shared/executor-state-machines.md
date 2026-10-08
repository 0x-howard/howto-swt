# Domain Executor State Machines

State identifies where the current task is inside its owning Executor. It is not the user's SWT lifecycle stage and is not a requirement to expose process labels in the answer. Skip a state when it adds no work; never add ceremony merely to visit every label.

## `swt-application`

`INTAKE -> SUBJECT_RESOLVE -> REQUIREMENTS -> MATERIAL_CHECK -> SUBMISSION_STATUS -> BLOCKER -> NEXT_ACTION`

- Resolve the agency, Sponsor, employer, system, or document before applying requirements.
- Distinguish prepared, submitted, under review, approved, and needs correction.
- Payment, signature, and final submission remain user-controlled.

## `swt-position`

`INTAKE -> NORMALIZE -> LOCATION_RESOLVE -> ANALYZE -> BUDGET -> RISK -> DECISION -> NEXT_ACTION`

- Normalize each offer independently; never borrow location or financial facts from another offer.
- Location and budget states are optional for a narrow question that does not need them.
- The Executor supports a decision but does not make the user's final value choice.

## `swt-english`

`PROFILE -> ASSESS | PRACTICE | MOCK | RECORDING | RETRY | PROGRESS -> RESULT | NEXT_PLAN`

- Enter at the state matching the user's six-mode intent; `GENERAL ENGLISH` remains a fallback, not a primary state.
- `PRACTICE` teaches immediately and may transition to `RETRY`; `MOCK` withholds teaching until its final `RESULT`.
- A Mock main question may transition through at most `FOLLOW_UP_1`, `FOLLOW_UP_2`, and `FOLLOW_UP_3`, then must move to the next main question. Clarification counts toward the same cap.
- `ASSESS`, completed `MOCK`, and `RECORDING` produce the same seven-dimension Assessment Result. Practice evidence never silently overwrites a formal result.
- Text or transcript input leaves pronunciation `not_assessed`; audio-dependent observations require actual media evidence.
- Visa facts remain owned by `swt-visa`; this Executor evaluates communication only after material facts are consistent.

## `swt-visa`

`INTAKE -> FACT_EXTRACTION -> CONSISTENCY_CHECK -> CONFLICT_OR_MISSING -> RISK -> NEXT_ACTION`

- `CONFLICT_OR_MISSING` is conditional: skip it when material facts are complete and consistent.
- Stop fact optimization when critical documents conflict.
- This Executor never predicts issuance or acts as the consular authority.

## `swt-arrival`

`SAFETY_CHECK -> INTAKE -> DEPENDENCY_ORDER -> ACTION -> CONFIRMATION -> NEXT_ACTION`

- Emergency safety checks can bypass ordinary intake.
- Order I-94, Sponsor check-in, SSN, insurance, job or housing changes by their real dependencies.
- Distinguish notified, submitted, system-confirmed, and approved.

## Transition rules

- Start only at a state defined for the selected Executor.
- Move forward, remain in the same state while gathering evidence, or return to an earlier state only when changed facts invalidate prior work.
- End with a concrete next action, a verified completion state, or a clearly named blocker.
- An Executor may not transition into another Executor's state machine. Cross-domain work returns to the Router as a supporting handoff.
