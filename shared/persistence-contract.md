# User Data and Persistence Contract

## Default behavior

Conversation state is temporary. Cross-conversation persistence is opt-in and is used only when the host or user explicitly configures an external `USER_DATA_ROOT`. There is no default directory, no automatic repository fallback, and no write to plugin source, references, assets, caches, or logs.

The adapter in `scripts/user_state.py` is a local JSON reference implementation. It does not enable a host to persist automatically. A host must explicitly call it for a user-requested load, save, update, or delete operation and explain the selected data boundary.

The Plugin manifest does not currently bind or configure `USER_DATA_ROOT`, and the ordinary Skill runtime does not automatically call this adapter. Persistence is available only to a host that deliberately launches the helper with the user's configured environment variable; otherwise cross-conversation persistence is unavailable.

## Storage boundary

- Resolve `USER_DATA_ROOT` as an absolute path outside the plugin source tree.
- Store only the allowlisted profile, stage, preference, Offer summary, English summary, verified Visa facts, and Arrival task fields in `references/user-state.schema.json`.
- Read only the one file `swt-user-state.json` under that root. Do not scan directories.
- Save atomically with owner-only permissions where supported. Never log data values.
- If the root is unset, relative, unavailable, inside the plugin source, or schema-invalid, do not silently choose another location. Keep state in the current conversation and tell the user persistence is unavailable.
- A user can request deletion by deleting that file or asking a host that supports deletion to remove it. Do not claim remote backups or host-managed copies were deleted unless verified.

## Explicit exclusions

Do not persist passwords, one-time codes, full passport or national ID numbers, date of birth, DS-160 confirmation numbers, SEVIS IDs, bank or payment details, signatures, document images, raw application forms, full addresses, private phone/email, or raw chat/voice transcripts. Do not put secrets into free-text summaries. For Visa, persist only a minimal factual summary the user explicitly approved, such as program year, sponsor name, role, and confirmed program dates; sensitive identifiers remain outside the plugin's data model.

## Data ownership

The user controls whether data is saved and which configured directory is used. Never treat files found beside the plugin as user profile data. Never infer consent to save from a user sharing information for a one-time task.
