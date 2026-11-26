# Interaction Adapter Capability Record

This record separates live/runtime evidence from contract tests. Capabilities must still be supplied by the active host session; the table is not a permanent allowlist.

| Host | Current evidence | Native capability conclusion | Verification level |
|---|---|---|---|
| Cursor | Product docs and agent skills require `AskQuestion`（交互式用户提问）for fixed-choice moments. Some Cursor agent sessions expose it; others only list AwaitShell/SwitchMode/Task and **do not** expose `AskQuestion`. | When `AskQuestion` is in the live tool list, `swt-position` assumption confirm and core-goal choice **must** call it. If missing from the session inventory, use numbered/text fallback and do not pretend a popup ran. | Per-session tool inventory; do not assume always available. |
| Codex | Current Codex session exposes structured `request_user_input` only in Plan mode; this task runs in Default mode where it is unavailable. | Default-mode adapter must use numbered/text fallback; Plan mode may map when the tool is actually exposed. | Current-session tool inventory verified; no picker invoked in this task. |
| Claude Code | Local reference material mentions `AskUserQuestion`; availability is session-dependent. | Map to `AskUserQuestion` only when present in the active session; otherwise fallback. | Contract/static + live inventory. |
| WorkBuddy | Installed WorkBuddy runtime and bundled Skill references explicitly use `AskUserQuestion`, including single, multi-select, and confirmation patterns. | Adapter may map to `AskUserQuestion` only when that tool is present in the active WorkBuddy session; otherwise fallback. | Installed-runtime static evidence; not live E2E. |
| Doubao Work | No callable Doubao Work interface or local runtime schema was found in this environment. | Numbered/text fallback. | Unverified live UI; contract only. |

**`swt-position` 测算前确认**：优先顺序为 Cursor `AskQuestion` → 宿主 `AskUserQuestion`／原生 choice → Markdown fallback。有交互提问工具却只发聊天编号选项，视为执行错误。

The canonical booleans are `supports_single_choice`, `supports_multi_choice`, `supports_free_text`, `supports_structured_form`, and `supports_confirmation`. Unknown is passed as `false`, never guessed as supported.
