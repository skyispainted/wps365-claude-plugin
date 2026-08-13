---
description: Execute WPS 365 authentication, initialization, and credential diagnostics. Use the existing App ID flow and never use OpenClaw.
argument-hint: [初始化、登录、检查或退出]
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
