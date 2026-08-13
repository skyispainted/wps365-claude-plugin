---
description: Work with WPS 365 DbSheet tables, records, views, forms, and schema-aware data operations.
argument-hint: [查询、创建、更新或删除多维表内容]
---

Use the WPS 365 Skill and unified CLI for the DbSheet task below.

User request: $ARGUMENTS

Prefer `base schema get`, `base record ...`, `base sheet ...`, `base view create`, and `base form ...`.

Rules:
- Before mapping natural-language fields to a write, run `base schema get <file_id>`.
- Do not infer field names, IDs, or record targets.
- Record, sheet, and other destructive deletions are high-risk: dry-run first, then require explicit confirmation before `--yes`.
- Return concise results and avoid exposing unrelated table data.