---
description: WPS 日历 / 协作日历 / WPS 日程：查看、创建、修改、删除日历和日程，管理参与者和忙闲时间。以上名称含义相同。
argument-hint: [例如：查看协作日历、创建会议日程、查询空闲时间]
---

Use the WPS 365 Skill and unified CLI for the calendar task below.

User request: $ARGUMENTS

Prefer `calendar calendar ...`, `calendar event ...`, and `calendar availability list`.

Rules:
- Use timezone-aware ISO 8601 times, such as `2026-08-12T09:00:00+08:00`.
- Resolve people with `contact +search <name>` before adding attendees when an ID is unavailable.
- Delete operations are high-risk: run `--dry-run`, show the target, then require explicit confirmation before `--yes`.
- Do not reauthenticate unless the CLI returns an authentication error.