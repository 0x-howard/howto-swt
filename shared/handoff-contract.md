# Skill-to-Skill Handoff Contract

HowTo SWT uses one semantic handoff shape between the `swt` Router and the five Domain Executors. The Router renders it as a directly-sendable user-facing prompt; it is an operational contract, not hidden chain of thought.

## Canonical shape

```yaml
handoff_version: "1.1"
router: swt
executor: swt-position
intent: DECISION
user_goal: compare two offers and choose the safer option
known_facts: {}
changed_facts: {}
missing_critical_facts: []
constraints: []
execution_cadence: analyze the supplied context, ask only decision-changing gaps, then complete the requested task
requested_output: decision with next action
state: INTAKE
```

All fields are required. `known_facts` contains only facts available to the current task. `changed_facts` contains later user corrections and overrides the same keys in `known_facts`. `missing_critical_facts` contains only gaps that prevent safe routing or execution. `constraints` contains user, safety, time, output, or evidence limits that materially affect the task. `execution_cadence` defines interaction rhythm, such as one question at a time, delayed Mock feedback, or immediate Practice feedback.

## User confirmation boundary

The main Router follows `Router → Handoff Prompt → STOP → user confirms/modifies/resends → Executor`. Once a route is known, it renders the full contract in a clearly delimited `HOWTO_SWT_HANDOFF_V1` block and stops. It must not call the Executor or begin its first action in the same turn. Receiving that user-sent block is the Executor's authorization to start.

The rendered prompt must name the selected Skill, current task, user goal, effective known facts, current corrections, constraints, execution cadence, and requested output. It may omit empty display sections but never omit their meaning. Promotional copy, edition labels, or upgrade messages are outside the block and are never part of this contract.

## Routing modes

- `DIRECT`: one Executor clearly owns the task and no fact required to choose that Executor is missing. Generate its Handoff Prompt immediately; do not show a menu or execute it first.
- `CONFIRM`: two to four materially plausible routes remain. Offer two to four short choices and wait for the user's selection.
- `CLARIFY`: a minimum fact required to choose a safe route is absent. Ask only the single highest-impact question; do not present a long intake form.

Missing facts needed inside an already selected Executor do not automatically change `DIRECT` to `CLARIFY`. The Executor may continue useful work and ask only what changes its conclusion, following the interaction protocol.

## Merge and evidence rules

1. Current-turn `changed_facts` overrides same-key `known_facts`; unchanged facts remain available.
2. Never request a key already present after that merge.
3. A correction is scoped to the current handoff unless an authorized persistent context layer explicitly writes it back.
4. Facts keep their evidence status. A correction does not automatically turn a pending or inferred value into a confirmed value.
5. Do not include raw transcripts, credentials, full identifiers, unnecessary document contents, or hidden reasoning.

## Executor contract

An Executor accepts only a user-confirmed or user-resent handoff addressed to its own Skill, starts at a valid state, performs domain work, and returns a compact result containing conclusion, material evidence or uncertainty, current state, blockers, and next action. It may request another specialist through the Router, but it must not silently take ownership of another domain.

The Router does not combine results in the handoff turn. It does not rewrite domain facts or perform the specialist's analysis. The rendered prompt may expose the operational fields needed for user confirmation, but never hidden reasoning.
