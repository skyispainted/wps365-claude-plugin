---
description: Work with WPS 365 calendars, events, attendees, availability, and calendar management.
argument-hint: [查看、创建、修改或删除日历和日程]
---

Use the WPS 365 Skill and unified CLI for the calendar task below.

User request: $ARGUMENTS

Prefer `calendar calendar ...`, `calendar event ...`, and `calendar availability list`.

Rules:
- Use timezone-aware ISO 8601 times, such as `2026-08-12T09:00:00+08:00`.
- Resolve people with `contact user search` before adding attendees when an ID is unavailable.
- Delete operations are high-risk: run `--dry-run`, show the target, then require explicit confirmation before `--yes`.
- Do not reauthenticate unless the CLI returns an authentication error.