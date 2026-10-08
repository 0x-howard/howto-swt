# Interaction Adapter Capability Record

This record separates live/runtime evidence from contract tests. Capabilities must still be supplied by the active host session; the table is not a permanent allowlist.

| Host | Current evidence | Native capability conclusion | Verification level |
|---|---|---|---|
| Codex | Current Codex session exposes structured `request_user_input` only in Plan mode; this task runs in Default mode where it is unavailable. | Default-mode adapter must use numbered/text fallback; Plan mode may map when the tool is actually exposed. | Current-session tool inventory verified; no picker invoked in this task. |
| Claude Code | No Claude CLI/runtime is installed or active on this machine. Local third-party reference material mentions `AskUserQuestion`, but that is not live evidence. | Conservative fallback until the active Claude runtime exposes its schema. | Contract/static reference only. |
| WorkBuddy | Installed WorkBuddy runtime and bundled Skill references explicitly use `AskUserQuestion`, including single, multi-select, and confirmation patterns. No active WorkBuddy conversation was invoked here. | Adapter may map to `AskUserQuestion` only when that tool is present in the active WorkBuddy session; otherwise fallback. | Installed-runtime static evidence; not live E2E. |
| Doubao Work | No callable Doubao Work interface or local runtime schema was found in this environment. | Numbered/text fallback. | Unverified live UI; contract only. |

The canonical booleans are `supports_single_choice`, `supports_multi_choice`, `supports_free_text`, `supports_structured_form`, and `supports_confirmation`. Unknown is passed as `false`, never guessed as supported.
