# Skill-to-Skill Handoff Contract

HowTo SWT uses one internal handoff shape between the `swt` Router and the five Domain Executors. It is a compact semantic contract, not a user-facing form and not hidden chain of thought.

## Canonical shape

```yaml
handoff_version: "1.0"
router: swt
executor: swt-position
intent: DECISION
user_goal: compare two offers and choose the safer option
known_facts: {}
changed_facts: {}
missing_critical_facts: []
constraints: []
requested_output: decision with next action
state: INTAKE
```

All fields are required. `known_facts` contains only facts available to the current task. `changed_facts` contains later user corrections and overrides the same keys in `known_facts`. `missing_critical_facts` contains only gaps that prevent safe routing or execution. `constraints` contains user, safety, time, output, or evidence limits that materially affect the task.

## Routing modes

- `DIRECT`: one Executor clearly owns the task and no fact required to choose that Executor is missing. Route immediately; do not show a menu first.
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

An Executor accepts only a handoff addressed to its own Skill, starts at a valid state, performs domain work, and returns a compact result containing conclusion, material evidence or uncertainty, current state, blockers, and next action. It may request another specialist through the Router, but it must not silently take ownership of another domain.

The Router may combine multiple Executor results into one response. It does not rewrite domain facts, perform the specialist's full analysis, or expose this YAML shape unless the user explicitly requests technical diagnostics.
