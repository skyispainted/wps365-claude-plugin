---
description: Work with WPS 365 chats and messages, including text, rich text, images, files, cards, history, search, and recalls.
argument-hint: [查看、搜索、发送或撤回消息]
---

Use the WPS 365 Skill and unified CLI for the messaging task below.

User request: $ARGUMENTS

Prefer `im chat ...`, `im recent list`, and `im message ...`.

Rules:
- Resolve an ambiguous chat before sending.
- Use `im message send` for text; use `send-rich`, `send-image`, `send-file`, or `send-card` for explicit JSON payloads.
- Do not invent `storage_key`, cloud-file metadata, mentions, or card fields. Use only user-provided or WPS-returned payload values.
- Message recall is high-risk: dry-run first, then require explicit confirmation before `--yes`.
- Do not disclose unrelated messages or chat metadata.
