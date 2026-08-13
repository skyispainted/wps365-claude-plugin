---
description: WPS 云文档操作：查看、搜索、读取、创建、上传、分享、标签、收藏和版本管理。适用于 WPS Drive / cloud documents。
argument-hint: [例如：查看最近文档、搜索项目方案、分享文件]
---

Use the WPS 365 Skill and unified CLI for the cloud-document task below.

User request: $ARGUMENTS

Prefer structured commands such as `drive directory list`, `drive file search/get/read`, `drive recent list`, `drive favorite list`, and `drive label ...`.

Rules:
- Use an exact file ID directly; search only when the user supplied a name rather than an ID.
- Resolve ambiguity before a write; never guess a file target.
- Use `drive file write` only for `.otl` smart documents.
- Use `drive file overwrite` or `drive file convert-overwrite` for non-`.otl` document versions; first use `--dry-run`, then require explicit confirmation before `--yes`.
- Treat move and share changes as high-risk. Pass fine-grained sharing parameters only when explicitly supplied.
- Summarize results without exposing unnecessary private metadata.