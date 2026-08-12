---
name: wps365
description: Use when the user asks to work with WPS 365, WPS 云文档、协作文档、金山文档, calendar, meeting, contacts, DbSheet, or WPS messages. Execute the requested operation with the unified `python -m wps365` CLI; do not claim WPS is inaccessible before the CLI returns an error.
---

# WPS 365

Use this Skill to perform WPS 365 operations. The only common command entry point is:

```bash
python -m wps365 <domain> <+shortcut> [flags]
```

For example, when the user asks to view the WPS cloud document list, run:

```bash
python -m wps365 drive +list
```

Return a concise summary of the CLI result. Do not say WPS is inaccessible, ask the user to export data, or suggest OpenClaw before running the CLI. If the CLI returns a structured error, explain that specific error and follow its hint.

## Authentication

Only check or recover authentication when the user explicitly asks to initialize WPS, or when a WPS command returns an `authentication` error:

```bash
python -m wps365 auth status --verify
```

- If the stored App ID exists but the SID is invalid, run `python -m wps365 auth login --flow local`.
- If no App ID is stored, ask only for the WPS 365 digital employee App ID, then run `python -m wps365 auth login --flow local --app-id <app_id>`.
- Keep the login command running while the user completes browser authorization, then run `python -m wps365 auth test`.
- Never install, require, or suggest OpenClaw.

## Direct routing

| User intent | Command |
|---|---|
| Find a person | `contact +search <name>` |
| View calendar / availability | `calendar +agenda` / `calendar +freebusy` |
| Create or change calendar events | `calendar +create` / `+update` / `+delete` |
| List, create, or cancel meetings | `meeting +list` / `+create` / `+cancel` |
| List, search, read, create, or upload documents | `drive +list` / `+search` / `+read` / `+create` / `+upload` |
| Edit, move, or share documents | `drive +write` / `+move` / `+share` |
| Read or write DbSheet data | `base +schema` / `+list` / `+create` / `+update` |
| Search chats, read history, or send messages | `im +search` / `+history` / `+send` |

Use `python -m wps365 schema [domain] [+shortcut]` only when the matching shortcut or its arguments are unclear. Commands return JSON: success is `{"ok": true, "data": ...}`; errors are JSON on stderr.

## Operational rules

1. Resolve ambiguous document names, people, chats, and share links before writing. Do not guess identifiers.
2. When a precise file ID is available, use `drive +get/+read <file_id>` directly. Use `--link-id` only for a sharing-link ID.
3. Before mapping natural-language DbSheet fields, run `base +schema <file_id>`.
4. Do not re-authenticate for validation, authorization, not-found, or ordinary upstream business errors.
5. Retry only errors marked `retryable: true`; never blindly retry a non-idempotent write.
6. Use timezone-aware ISO 8601 times, for example `2026-08-12T09:00:00+08:00`.

## Confirming high-risk writes

For deletions, meeting cancellation, message recall, document moves, or sharing changes:

1. Run the same command with `--dry-run`.
2. Present the resolved target to the user.
3. After explicit confirmation of that action, run it again with `--yes`.

Without confirmation, do not add `--yes`. Unsupported low-frequency operations can use:

```bash
python -m wps365 legacy <domain> <legacy-command> [arguments]
```

## References

- Documents and sharing links: `references/drive.md`
- Calendars and meetings: `references/calendar-meeting.md`
- DbSheet structure and records: `references/dbsheet.md`
- Chats and messages: `references/im.md`
