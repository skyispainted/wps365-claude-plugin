---
description: WPS 云文档 / 协作文档 / 金山文档：查看、搜索、读取、创建、上传、分享、标签、收藏和版本管理。以上名称含义相同。
argument-hint: [例如：查看最近协作文档、搜索项目方案、分享文件]
---

Use the WPS 365 Skill and unified CLI for the cloud-document task below.

User request: $ARGUMENTS

Prefer `drive +list/+search/+get/+read`, `drive +recent`, `drive +favorite-*`, and `drive +label-*`.

Rules:
- Use an exact `link_id` with `drive +get/+read --link-id <link_id>`; `--link-id` requires a value.
- Use an exact file ID directly only when it is a verified own-file reference.
- After `drive +search`, reuse the selected result's `read_args` exactly. Shared-link results use `--link-id <link_id>`; do not assume their `id` is readable through the private drive.
- Resolve ambiguity before reading or writing; never guess a file target or switch to a different search result after failure.
- Use `drive +write` only for `.otl` smart documents.
- Use `drive +overwrite` or `drive +convert-overwrite` for non-`.otl` document versions; first use `--dry-run`, then require explicit confirmation before `--yes`.
- Treat move and share changes as high-risk. Pass fine-grained sharing parameters only when explicitly supplied.
- Summarize results without exposing unnecessary private metadata.