# Cross-Agent Interaction Capability Layer

This shared semantic layer is the single source of truth for `swt` and all five Domain Executors. Skills describe an `Interaction Request`; a host adapter chooses a real UI only when the current runtime exposes it. No Skill hardcodes Codex, Claude Code, WorkBuddy, or Doubao APIs.

## Priority and routing

1. **Direct execution** — the task and required facts are already clear. Never show a choice merely to look interactive.
2. **Interactive choice** — a user must select among finite alternatives.
3. **Structured input** — one or more concrete facts must be entered.
4. **Open-ended text** — only when the first three cannot express the needed information.

`DIRECT` returns no Interaction Request. `CONFIRM` prefers a choice or explicit confirmation. For `CLARIFY`, a finite enum uses choice; a free-form fact uses free text or a structured form. Confirmed context is reused and not requested again. Conflicts, multiple reasonable actions, and high-impact authorization may still require interaction.

## Interaction Request schema

```json
{
  "interaction_version": "1.0",
  "type": "single_choice",
  "id": "next_action",
  "question": "你现在想先处理哪一步？",
  "options": [
    {"id": "position", "label": "分析 / 对比岗位", "description": "比较收入、成本和风险"},
    {"id": "english", "label": "准备英语面试", "description": "进入英语训练"}
  ],
  "fields": [],
  "min_selections": 1,
  "max_selections": 1,
  "allow_other": true,
  "recommended_option_id": null,
  "recommendation_basis": null,
  "sensitive_confirmation": false
}
```

Types are `single_choice`, `multi_choice`, `free_text`, `structured_form`, and `confirmation`. A form field uses `{id, label, required}`. Options normally contain two to four items. More than four must be grouped, filtered, searched, or paged; the explicit exception is Offer ROI selection, which lists every Offer and caps selection at three. `allow_other` opens free text. A recommended option requires a concise basis derived from known facts, state, or deterministic decision logic.

## Host capability contract

Every runtime adapter reports booleans for `supports_single_choice`, `supports_multi_choice`, `supports_free_text`, `supports_structured_form`, and `supports_confirmation`, plus the actually exposed tool/interface name. Capabilities are observations of the current session, not permanent product claims.

- If the exact requested native capability is available, map the semantic request to that interface.
- If unavailable or unknown, use the shared numbered/text fallback.
- Markdown checkboxes are text, not a native picker.
- Contract/mocked adapter tests prove mapping only; live UI verification must be recorded separately.

## Fallbacks

Single choice is numbered and ends with “回复数字即可。” Multi-choice states its maximum and accepts comma-separated numbers. Confirmation is exactly `1. 继续 / 2. 取消`. Free text asks the concrete fact directly. Structured forms without native support list their field labels and accept a compact text response.

Cancellation returns `cancelled` and performs no downstream action. Invalid or over-limit selections return a validation error and preserve the same request.

## Safety and persistence

Interaction UI does not weaken authorization. Edition replacement and other sensitive/high-impact actions always require a fresh explicit confirmation, even if an earlier message requested installation. Pro Context Builder suppresses questions whose answers are already confirmed; inference does not count as confirmed context.

## Shared Executor uses

- `swt-position`: more than three offers → `multi_choice`, maximum three.
- `swt-english`: genuinely undecided practice mode → `single_choice`; a named mode stays direct.
- `swt-visa`: multiple valid next actions → `single_choice`; one required next action stays direct.
- `swt-application`: finite stage confirmation → `single_choice`; a missing document value uses free text.
- `swt-arrival`: multiple valid action paths → `single_choice`; emergencies bypass ordinary choice.

These are semantic examples, not copies to paste into five Skill files.
