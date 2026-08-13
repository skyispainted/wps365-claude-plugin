---
description: Work with WPS 365 cloud documents, folders, links, shares, labels, favorites, and document version updates.
argument-hint: [查看、搜索、读取、创建、上传、分享或管理云文档]
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