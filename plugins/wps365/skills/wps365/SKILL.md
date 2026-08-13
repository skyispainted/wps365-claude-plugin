---
name: wps365
description: Use when the user asks to work with WPS 365, WPS 云文档、协作文档、金山文档, calendar, meeting, contacts, DbSheet, or WPS messages. Execute the requested operation with the unified `python -m wps365` CLI; do not claim WPS is inaccessible before the CLI returns an error.
---

# WPS 365

## 初始化（代理必须自主完成）

当用户说“初始化”“配置 WPS 365”或首次要求 WPS 能力时，代理必须自主完成初始化，不得只把命令发给用户让其自行执行。除提供 App ID 和在浏览器中完成 WPS 授权外，不要求用户手动操作。

### 执行流程

1. 检查 Python、`cryptography` 和统一 CLI 是否可用；缺少 Python 依赖时自动安装到用户环境。
2. 运行 `python -m wps365 auth status`，读取已保存的 App ID 和凭证状态；不得输出 App ID、SID、凭证文件内容或加密材料。
3. 运行 `python -m wps365 auth status --verify` 验证现有凭证。只有 `verified: true` 才算认证有效；仅“已配置”但验证失败不能算初始化完成。
4. 如果凭证有效，直接报告已完成并继续用户原始任务，不重复登录、不再次索要 App ID。
5. 如果 SID 失效但已有 App ID，自动复用已保存 App ID，执行：

```bash
python -m wps365 auth login --flow local
```

6. 如果没有已保存的 App ID，只向用户询问 WPS 365 数字员工 App ID；取得后代理立即执行：

```bash
python -m wps365 auth login --flow local --app-id <app_id>
```

7. 本地授权命令运行期间保持等待。用户只需要在浏览器中完成 WPS 授权，不要要求用户复制 OAuth code、state 或 SID。
8. OAuth 命令返回后立即执行：

```bash
python -m wps365 auth test
```

只有认证测试成功才报告初始化完成；认证失败时说明结构化错误，不要伪造成功。
9. 初始化完成后继续执行用户最初请求的 WPS 任务，不要停在“初始化成功”而遗漏原任务。
10. 初始化诊断失败时可执行：

```bash
python -m wps365 config doctor
```

**认证约束：** 使用 WPS 365 App ID 和现有加密凭证存储机制。不要安装、要求安装、提示开通或依赖 OpenClaw。

## 常规操作


```bash
python -m wps365 <domain> <+shortcut> [flags]
```

For example, when the user asks to view the WPS cloud document list, run:

```bash
python -m wps365 drive +list
```

Return a concise summary of the CLI result. Do not say WPS is inaccessible, ask the user to export data, or suggest OpenClaw before running the CLI. If the CLI returns a structured error, explain that specific error and follow its hint.

## Authentication

Only check or recover authentication when the user explicitly asks to initialize WPS, or when a WPS command returns an `authentication` error:

```bash
python -m wps365 auth status --verify
```

- If the stored App ID exists but the SID is invalid, run `python -m wps365 auth login --flow local`.
- If no App ID is stored, ask only for the WPS 365 digital employee App ID, then run `python -m wps365 auth login --flow local --app-id <app_id>`.
- Keep the login command running while the user completes browser authorization, then run `python -m wps365 auth test`.
- Never install, require, or suggest OpenClaw.

## Direct routing

| User intent | Command |
|---|---|
| Find a person | `contact +search <name>` |
| View calendar / availability | `calendar +agenda` / `calendar +freebusy` |
| Create or change calendar events | `calendar +create` / `+update` / `+delete` |
| List, create, or cancel meetings | `meeting +list` / `+create` / `+cancel` |
| List, search, read, create, or upload documents | `drive +list` / `+search` / `+read` / `+create` / `+upload` |
| Edit, move, or share documents | `drive +write` / `+move` / `+share` |
| Read or write DbSheet data | `base +schema` / `+list` / `+create` / `+update` |
| Search chats, read history, or send messages | `im +search` / `+history` / `+send` |

Use `python -m wps365 schema [domain] [+shortcut]` only when the matching shortcut or its arguments are unclear. Commands return JSON: success is `{"ok": true, "data": ...}`; errors are JSON on stderr.

## Operational rules

1. Resolve ambiguous document names, people, chats, and share links before writing. Do not guess identifiers.
2. When a precise file ID is available, use `drive +get/+read <file_id>` directly. Use `--link-id` only for a sharing-link ID.
3. Before mapping natural-language DbSheet fields, run `base +schema <file_id>`.
4. Do not re-authenticate for validation, authorization, not-found, or ordinary upstream business errors.
5. Retry only errors marked `retryable: true`; never blindly retry a non-idempotent write.
6. Use timezone-aware ISO 8601 times, for example `2026-08-12T09:00:00+08:00`.

## Confirming high-risk writes

For deletions, meeting cancellation, message recall, document moves, or sharing changes:

1. Run the same command with `--dry-run`.
2. Present the resolved target to the user.
3. After explicit confirmation of that action, run it again with `--yes`.

Without confirmation, do not add `--yes`. Unsupported low-frequency operations can use:

```bash
python -m wps365 legacy <domain> <legacy-command> [arguments]
```

## References

- Documents and sharing links: `references/drive.md`
- Calendars and meetings: `references/calendar-meeting.md`
- DbSheet structure and records: `references/dbsheet.md`
- Chats and messages: `references/im.md`
