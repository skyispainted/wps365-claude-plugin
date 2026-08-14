---
description: WPS 消息 / 协作消息 / WPS 会话：查看、搜索、发送或撤回文本、富文本、图片、文件和卡片消息。以上名称含义相同。
argument-hint: [例如：查找协作会话、发送消息、撤回消息]
---

Use the WPS 365 Skill and unified CLI for the messaging task below.

User request: $ARGUMENTS

Prefer `im +list/+get/+search/+recent/+history/+message-search`.

Rules:
- If a precise `chat_id` is already known, send directly. Otherwise resolve the person with `contact +search <name>`, then select only a `p2p` chat whose peer ID matches that contact; never guess a group chat.
- Resolve an ambiguous person or chat before sending.
- Use `im +send` for text; use `+send-rich`, `+send-image`, `+send-file`, or `+send-card` for explicit JSON payloads.
- Do not invent `storage_key`, cloud-file metadata, mentions, or card fields. Use only user-provided or WPS-returned payload values.
- Message recall is high-risk: dry-run first, then require explicit confirmation before `--yes`.
- Do not disclose unrelated messages or chat metadata.
