---
name: wps365
description: WPS 365 V7 API 工具集。用于查询通讯录、管理日历日程、创建会议、操作云文档、管理多维表、发送聊天消息等企业协作任务。当用户提到通讯录、日程、会议、云文档、多维表、发消息、查人、创建文档等需求时使用。
---

# WPS 365 技能工具集

## 初始化（代理必须自主完成）

用户说"初始化""配置 WPS 365"或首次要求 WPS 能力时，代理必须自行完成初始化，不得只发送命令让用户执行。除 App ID 和浏览器中的 WPS 授权外，不得要求用户手动操作。

### 执行步骤

1. 检查 Python 和 `cryptography`；缺失时安装依赖。
2. 将当前插件的 `wpsv7client` 和 `wps_credential_manager` 覆盖同步到用户 site-packages，然后验证导入成功。
3. 运行 `python -m wps_credential_manager status` 和 `python -m wps_credential_manager test`。只有 `test` 返回"sid 有效"才算初始化完成；"已配置"但测试失败仍须重新授权。
4. 凭证有效时，直接报告成功并继续原始任务，不重新登录、不索要 App ID。
5. 凭证缺失或失效时：若 `status` 有 `app_id`，自动复用；否则只询问用户提供 WPS 365 数字员工 App ID（例如 `AK20260501LJGRPT`）。
6. 得到 App ID 后，代理自行执行：

```bash
python -m wps_credential_manager login --flow local --app-id <app_id>
```

7. 命令监听 `http://127.0.0.1:11791/oauth-callback` 并打开浏览器。保持命令运行，仅提示用户在浏览器完成授权；命令返回后立即运行 `python -m wps_credential_manager test`，仅在通过时报告初始化成功。
8. 用户仅要求云文档时，认证成功后继续执行云文档任务；业务参数错误应与认证错误区分，不得反复要求重新登录。

本 skill 使用 WPS 365 数字员工 App ID 认证。**不要安装、要求安装或提示开通 OpenClaw。** 桌面环境默认使用 `local` 回调；仅在无法访问本机浏览器回调的远程环境使用 `cloud`。

### 包同步命令

**Linux / macOS:**

```bash
python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM" 2>/dev/null || pip install cryptography; USER_SITE=$(python -c "import site; print(site.getusersitepackages())"); mkdir -p "$USER_SITE"; PLUGIN_DIR=$(find ~/.claude/plugins/cache/wps365-marketplace/wps365 -maxdepth 4 -type d -name scripts 2>/dev/null | head -1); [ -n "$PLUGIN_DIR" ] && cp -a "$PLUGIN_DIR/wpsv7client" "$USER_SITE/" && cp -a "$PLUGIN_DIR/wps_credential_manager" "$USER_SITE/"; python -c "from wpsv7client import get_current_user; print('wps365 ready')"
```

**Windows PowerShell:**

```powershell
$USER_SITE = python -c "import site; print(site.getusersitepackages())"; if (-not (Test-Path $USER_SITE)) { New-Item -ItemType Directory -Path $USER_SITE -Force | Out-Null }; $PLUGIN_DIR = Get-ChildItem -Recurse -Directory -Filter scripts -ErrorAction SilentlyContinue "$env:USERPROFILE\.claude\plugins\cache\wps365-marketplace\wps365" | Select-Object -First 1 -ExpandProperty FullName; if (-not $PLUGIN_DIR) { throw "未找到 WPS 365 插件脚本目录" }; Copy-Item -Recurse -Force "$PLUGIN_DIR\wpsv7client" "$USER_SITE\"; Copy-Item -Recurse -Force "$PLUGIN_DIR\wps_credential_manager" "$USER_SITE\"; python -c "from wpsv7client import get_current_user; print('wps365 ready')"
```

## 凭证管理

```bash
python -m wps_credential_manager status   # 查看当前凭证状态
python -m wps_credential_manager refresh  # 手动刷新 token（默认 cloud 模式）
python -m wps_credential_manager logout   # 清除凭证（重新登录）
python -m wps_credential_manager test     # 测试凭证是否有效
```

## Python API

所有函数通过 `from wpsv7client import <函数名>` 直接导入。
所有函数返回格式统一为 `{"code": 0, "msg": "...", "data": {...}}`，调用方须先判断 `code == 0`，再从 `data` 中取值。

### 当前用户

```python
from wpsv7client import get_current_user
resp = get_current_user()
if resp.get("code") == 0:
    user = resp["data"]
    print(user["name"])
```

### 通讯录

```python
from wpsv7client import search_users
resp = search_users("姓名")
```

### 日历

```python
from wpsv7client import list_calendars, list_events, create_event

resp = list_calendars()
resp = list_events("calendar_id",
    start_time="2026-05-11T09:00:00+08:00",
    end_time="2026-05-12T09:00:00+08:00")
resp = create_event("calendar_id",
    start_time="2026-05-11T14:00:00+08:00",
    end_time="2026-05-11T15:00:00+08:00",
    summary="评审会议",
    attendee_user_ids=["user_id1", "user_id2"])
```

### 会议

```python
from wpsv7client import list_meetings, create_meeting

resp = list_meetings()
resp = create_meeting(
    subject="评审会议",
    start_time="2026-05-11T14:00:00+08:00",
    end_time="2026-05-11T15:00:00+08:00",
    participant_ids=["user_id1"])
```

### 云文档

```python
from wpsv7client import list_files, get_file

resp = list_files()
resp = get_file(drive_id="private", file_id="xxx")
```

### 多维表

```python
from wpsv7client import dbsheet_get_schema, dbsheet_list_records, dbsheet_batch_create_records

resp = dbsheet_get_schema("file_id")
resp = dbsheet_list_records("file_id", sheet_id=1)
records = [{"fields": {"姓名": "张三", "部门": "研发"}}]
resp = dbsheet_batch_create_records("file_id", sheet_id=1, records=records)
```

### 即时消息

**给某人发消息（完整流程）：**

```python
from wpsv7client import search_users, create_chat, send_message

# 1. 按姓名搜索用户，获取 user_id
resp = search_users("张冬")
user_id = resp["data"]["items"][0]["id"]

# 2. 创建单聊会话（p2p），注意 account_id_list 包含自己和对方
resp = create_chat(account_id_list=["1498584513", user_id], chat_type="p2p")
chat_id = resp["data"]["chat"]["id"]

# 3. 发送消息（只需传 chat_id 和 text）
resp = send_message(chat_id, text="1111")
```

其他 IM 功能：

```python
from wpsv7client import get_chat_list, list_chat_messages, send_message, list_recent_chats, search_chats

resp = get_chat_list()              # 列出会话
resp = list_recent_chats()          # 最近会话
resp = search_chats("关键词")        # 搜索会话
resp = list_chat_messages(chat_id)  # 列出消息
resp = send_message(chat_id, text="Hello")           # 发送纯文本
resp = send_message(chat_id, text="# 标题", text_type="markdown")  # 发送 markdown
```

## 时间格式

所有时间参数必须带时区：
- `2026-05-11T09:00:00+08:00`（东八区）
- `2026-05-11T01:00:00Z`（UTC）

禁止使用无时区格式如 `2026-05-11T09:00:00`。

## 错误处理

- API 调用须检查 `resp.get("code") == 0`，非 0 时 `resp["msg"]` 包含错误信息。
- 如果返回认证错误（401 / csrfCheckFailed / NOT_LOGIN），自动刷新凭证后重试。
- 如果刷新失败，提示用户重新运行 `python -m wps_credential_manager login`。
