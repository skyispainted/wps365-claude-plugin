---
description: WPS 365 认证与初始化：登录、凭证检查、诊断和退出。使用现有 App ID 流程，不使用 OpenClaw；关键词 auth / login / credentials。
argument-hint: [例如：初始化、登录、检查认证状态]
---

Use the WPS 365 Skill and unified CLI for authentication tasks.

User request: $ARGUMENTS

Rules:
- For initialization, follow the complete autonomous initialization flow in `/wps365`.
- Use `python -m wps365 auth status --verify`, `auth login --flow local`, `auth test`, and `config doctor` as appropriate.
- Ask for the WPS 365 digital employee App ID only when no stored App ID exists.
- Never expose App ID, SID, OAuth code/state, credential files, or encryption material.
- Never install, suggest, require, or depend on OpenClaw.
- After authentication succeeds, continue the user's original WPS task if one was included.
