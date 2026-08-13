---
description: WPS 日历与日程：查看、创建、修改、删除日历和日程，管理参与者和忙闲时间。关键词 calendar / event / availability。
argument-hint: [例如：查看今天日程、创建会议日程、查询空闲时间]
---

Use the WPS 365 Skill and unified CLI for the calendar task below.

User request: $ARGUMENTS

Prefer `calendar calendar ...`, `calendar event ...`, and `calendar availability list`.

Rules:
- Use timezone-aware ISO 8601 times, such as `2026-08-12T09:00:00+08:00`.
- Resolve people with `contact user search` before adding attendees when an ID is unavailable.
- Delete operations are high-risk: run `--dry-run`, show the target, then require explicit confirmation before `--yes`.
- Do not reauthenticate unless the CLI returns an authentication error.