---
description: WPS 会议 / 协作会议：查看、创建和管理会议、参会人、会议室、录制、纪要、转写、摘要与导出。以上名称含义相同。
argument-hint: [例如：创建协作会议、查看录制、导出会议纪要]
---

Use the WPS 365 Skill and unified CLI for the meeting task below.

User request: $ARGUMENTS

Prefer `meeting meeting ...`, `meeting participant ...`, `meeting room-level list`, `meeting recording ...`, and `meeting minute ...`.

Rules:
- Use timezone-aware ISO 8601 times for meeting schedules and time-range queries.
- Meeting cancellation is high-risk: dry-run first, then require explicit confirmation before `--yes`.
- For batch artifact exports, require a user-specified `--output-dir`; output JSON only and never overwrite an existing export file.
- Summaries and transcripts can be sensitive: disclose only what the user requested.