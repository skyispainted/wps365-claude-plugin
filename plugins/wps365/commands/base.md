---
description: WPS 多维表 / 协作多维表 / DbSheet：查询、创建、更新和删除数据表、记录、视图与表单，按 schema 安全写入。以上名称含义相同。
argument-hint: [例如：查询协作多维表记录、创建数据表、更新表单]
---

Use the WPS 365 Skill and unified CLI for the DbSheet task below.

User request: $ARGUMENTS

Prefer `base schema get`, `base record ...`, `base sheet ...`, `base view create`, and `base form ...`.

Rules:
- Before mapping natural-language fields to a write, run `base schema get <file_id>`.
- Do not infer field names, IDs, or record targets.
- Record, sheet, and other destructive deletions are high-risk: dry-run first, then require explicit confirmation before `--yes`.
- Return concise results and avoid exposing unrelated table data.