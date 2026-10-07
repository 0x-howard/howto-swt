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

`ASSESS -> DIAGNOSE -> PRACTICE -> RETRY -> REASSESS`

- Enter at the state matching the user's intent; ordinary roleplay need not start with `ASSESS`.
- Practice evidence never overwrites a formal assessment.
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
