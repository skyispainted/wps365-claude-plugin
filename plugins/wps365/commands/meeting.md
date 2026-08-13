---
description: Work with WPS 365 meetings, participants, meeting rooms, recordings, minutes, transcripts, summaries, and exports.
argument-hint: [查看、创建、管理或导出会议内容]
---

Use the WPS 365 Skill and unified CLI for the meeting task below.

User request: $ARGUMENTS

Prefer `meeting meeting ...`, `meeting participant ...`, `meeting room-level list`, `meeting recording ...`, and `meeting minute ...`.

Rules:
- Use timezone-aware ISO 8601 times for meeting schedules and time-range queries.
- Meeting cancellation is high-risk: dry-run first, then require explicit confirmation before `--yes`.
- For batch artifact exports, require a user-specified `--output-dir`; output JSON only and never overwrite an existing export file.
- Summaries and transcripts can be sensitive: disclose only what the user requested.