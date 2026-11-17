# kestrel-assistant 2026.11.10 (deployed 2026-11-10 06:10 PT)

- Tools are now enabled from a feature-flag set (`ENABLED_TOOLS`), so a tool can be switched off
  without a code change. Previously the tool list was a hard-coded Python list.
- New tool `store_hours`.
- The user turn now starts with `[context: store <id>, current time <timestamp>]` so the model can
  answer opening-hours questions.
- No change to the system prompt text or the cache breakpoint.
