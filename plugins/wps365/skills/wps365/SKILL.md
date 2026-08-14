---
name: wps365
description: WPS 365 综合操作：WPS 云文档、协作文档、金山文档、WPS Drive；WPS 联系人、协作联系人、企业通讯录；WPS 日历、协作日历；WPS 会议、协作会议；WPS 多维表和协作消息。使用当前插件随附的统一 WPS CLI 执行请求；在 CLI 返回错误前不得声称无法访问 WPS。
---

# WPS 365

Use the unified CLI for WPS 365 documents, calendars, meetings, contacts, DbSheet, and messages. Execute the user’s requested WPS operation; do not substitute generic instructions when the CLI can perform it.

可见的领域入口：`/wps365:auth`、`/wps365:drive`、`/wps365:calendar`、`/wps365:meeting`、`/wps365:im`、`/wps365:base`、`/wps365:contact`。它们提供同一 CLI 的定向路由；`/wps365:wps365` 保留为完整的跨领域入口。

## 运行入口

每次 CLI 调用必须使用当前插件随附的版本，避免用户 Python 环境中的旧 `wps365` 包覆盖新功能：

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/wps365/scripts/run_wps365.py" <arguments>
```

下文为简洁起见将其写成 `wps365 <arguments>`；这始终表示上面的完整命令，不表示直接运行可能过期的 `python -m wps365`。

## 同义名称路由

以下表达含义相同，应直接路由到同一 WPS 能力，不要求用户换词或重复说明：

| 用户表达 | 统一领域 |
| --- | --- |
| WPS 云文档、协作文档、金山文档、企业文档、WPS Drive | `drive` |
| WPS 联系人、协作联系人、企业联系人、企业通讯录、同事 | `contact` |
| WPS 日历、协作日历、WPS 日程、协作日程、我的日程 | `calendar` |
| WPS 会议、协作会议、在线会议、预约会议、会议室 | `meeting` |
| WPS 多维表、协作多维表、在线表格、DbSheet | `base` |
| WPS 消息、协作消息、WPS 会话、聊天、群消息 | `im` |

“协作”是 WPS 365 业务域的别名，不表示需要额外认证、切换账号或改用其他服务。

## 初始化（代理必须自主完成）

当用户说“初始化”“配置 WPS 365”或首次要求 WPS 能力时，代理必须自主完成初始化，不得只把命令发给用户让其自行执行。除提供 App ID 和在浏览器中完成 WPS 授权外，不要求用户手动操作。

### 执行流程

1. 检查 Python、`cryptography` 和统一 CLI 是否可用；缺少 Python 依赖时自动安装到用户环境。
2. 运行 `wps365 auth status`，读取已保存的 App ID 和凭证状态；不得输出 App ID、SID、凭证文件内容或加密材料。
3. 运行 `wps365 auth status --verify` 验证现有凭证。只有 `verified: true` 才算认证有效；仅”已配置”但验证失败不能算初始化完成。
4. 如果凭证有效，直接报告已完成并继续用户原始任务，不重复登录、不再次索要 App ID。
5. 如果 SID 失效但已有 App ID，自动复用已保存 App ID，执行：

```bash
wps365 auth login --flow local
```

6. 如果没有已保存的 App ID，只向用户询问 WPS 365 数字员工 App ID；取得后代理立即执行：

```bash
wps365 auth login --flow local --app-id <app_id>
```

7. 本地授权命令运行期间保持等待。用户只需要在浏览器中完成 WPS 授权，不要要求用户复制 OAuth code、state 或 SID。
8. OAuth 命令成功返回的 `verified: true` 即完成认证验证；不要紧接着重复运行 `wps365 auth test`。
9. 初始化完成后继续执行用户最初请求的 WPS 任务，不要停在”初始化成功”而遗漏原任务。
10. 仅在用户明确要求诊断或认证失败需要排查时执行：

```bash
wps365 config doctor
```

**认证约束：** 使用 WPS 365 App ID 和现有加密凭证存储机制。不要安装、要求安装、提示开通或依赖 OpenClaw。

## 命令模型

稳定公共契约使用 `+` 快捷命令：

```bash
wps365 <domain> <+shortcut> [flags]
```

当前插件内置 CLI 同时支持结构化路径（`wps365 <domain> <resource> <action> [flags]`），但默认优先快捷命令，避免旧的手工安装 CLI 不认识新结构化路径而产生无效探测。

```bash
wps365 drive +recent
wps365 drive +read <file_id>
wps365 drive +read --link-id <link_id>
wps365 calendar +agenda --start <ISO-8601> --end <ISO-8601>
wps365 base +list <file_id> <sheet_id>
wps365 im +message-search "关键词"
```

所有常用命令输出 JSON：成功为 `{"ok": true, "data": ...}`，失败为 stderr JSON。仅在快捷命令未知、CLI 返回"未知快捷命令"或参数契约仍不明确时使用发现：

```bash
wps365 schema <domain>
wps365 schema <domain> <+shortcut>
```

不要在每次请求前运行 `schema`、认证检查、目录枚举或多次搜索；已有精确 ID 时直接执行目标命令。

## 资源路由

| 用户目标 | 首选命令 |
| --- | --- |
| 搜索企业成员 | `contact +search <name>` |
| 列出、创建或管理日历 | `calendar +calendar-list/+calendar-create/+calendar-update/+calendar-delete` |
| 查询或创建日程 | `calendar +agenda/+get/+create/+update/+delete` |
| 查找空闲时间 | `calendar +freebusy` |
| 查询或管理预约会议 | `meeting +list/+get/+create/+update/+cancel` |
| 管理会议参会人 | `meeting +participant-list/+participant-add/+participant-remove` |
| 查询会议室 | `meeting +room-level-list`、`meeting +event-room-list` |
| 浏览、搜索、读取云文档 | `drive +list/+search/+get/+read` |
| 创建、上传、编辑或移动文档 | `drive +create/+upload/+write/+copy/+move/+rename` |
| 覆盖非 `.otl` 或转换 Markdown 后覆盖 | `drive +overwrite`、`drive +convert-overwrite` |
| 设置精细分享权限 | `drive +share --scope <scope> --role-id <role> --opts '<JSON>'` |
| 查看最近、收藏和回收站文档 | `drive +recent`、`drive +favorite-list`、`drive +trash-list` |
| 下载地址、文件名检查、标签 | `drive +download-url`、`drive +name-check`、`drive +label-*` |
| 查看多维表结构和记录 | `base +schema/+list/+get/+search` |
| 管理多维表数据表、视图、表单 | `base +sheet-*`、`base +view-create`、`base +form-get/+form-update` |
| 查询会话或消息 | `im +list/+get/+search/+recent/+history/+message-search` |
| 发送文本、富文本、图片、文件或卡片 | `im +send/+send-rich/+send-image/+send-file/+send-card` |
| 查看或导出会议录制、纪要、摘要和转写 | `meeting +recording-*`、`meeting +minute-*`、`meeting +artifact-export` |
| 撤回消息 | `im +recall` |

## 执行规则

1. 先选择单个最直接、风险最低的命令。只有结果不足以继续时才发起下一次查询。
2. 用户给出明确的分享链接或 `link_id` 时，直接使用 `drive +get/+read --link-id <link_id>`；`--link-id` 必须带值。仅对已验证的自有文件 ID 使用 `drive +get/+read <file_id>`。
3. 用户只给文档名称时，先 `drive +search <keyword>`；单一候选时原样复用返回的 `read_args`，多个候选时展示名称、来源和更新时间并让用户选择，不能猜测目标或重搜。
4. 共享来源（`file_src.type: "link"`）的搜索结果优先使用其 `read_args` / `--link-id <link_id>`，不要将 `id` 一律作为可读文件 ID。ID 读取失败且同一结果含 `link_id` 时，仅用该 `link_id` 重试一次；不要先运行 `schema`、重新认证或改用其他候选。
5. 写入 DbSheet 前先 `base +schema <file_id>`，再按真实字段名构造数据；不要凭自然语言臆测字段。
6. 需要人员 ID 时，先 `contact +search <name>`；找到多个同名人时请求消歧。
7. 时间必须使用含时区的 ISO 8601，例如 `2026-08-12T09:00:00+08:00`。
8. 用户需要结果摘要时，先完成读取，再以简洁形式总结；不要输出 App ID、SID、OAuth 回调参数、凭证文件、加密材料或不必要的私有字段。
9. 富媒体、文件和卡片消息使用对应 `im +send-rich/+send-image/+send-file/+send-card` 命令；只传递用户明确提供或已由 WPS 返回的 JSON 载荷，不要虚构 `storage_key`、成员身份或卡片字段。
10. 会议工件批量导出必须使用用户明确指定的 `--output-dir`；导出结果为 JSON，遇到同名文件时停止而非覆盖。

## 写入与确认

- **读取：** 直接执行。
- **普通写入：** 当目标、操作和内容清楚时直接执行；不清楚则只询问缺失的必要信息。
- **高风险写入：** 删除日程/日历/数据表/记录、取消会议、移动文件、覆盖非 `.otl` 文档、开启或关闭分享、撤回消息。先运行同一命令并追加 `--dry-run`，展示受影响目标；获得明确确认后以相同参数追加 `--yes` 执行。

不要把“准备执行”误报为完成。CLI 返回认证、权限、网络或 API 错误时，基于结构化错误采取最小修复动作并如实报告。

## 兼容入口

旧脚本仅作为未迁移能力的显式回退入口：

```bash
wps365 legacy <domain> <legacy-command> [arguments]
```

不要优先使用 `legacy`；优先统一 CLI 的结构化命令或等价 `+` 快捷命令。`legacy im recall` 已禁用，因为它无法提供统一 CLI 的确认保护；请使用 `im +recall` 的 dry-run/`--yes` 流程。

## References

- 云文档读写、分享和格式限制：`references/drive.md`
- 日程、会议、时区和会议室：`references/calendar-meeting.md`
- 多维表 schema-first 写入：`references/dbsheet.md`
- 会话、消息和撤回确认：`references/im.md`
