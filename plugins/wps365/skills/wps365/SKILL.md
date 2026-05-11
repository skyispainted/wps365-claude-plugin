---
name: wps365
description: WPS 365 V7 API 工具集。用于查询通讯录、管理日历日程、创建会议、操作云文档、管理多维表、发送聊天消息等企业协作任务。当用户提到通讯录、日程、会议、云文档、多维表、发消息、查人、创建文档等需求时使用。
---

# WPS 365 技能工具集

## ⚠️ 必须先执行初始化

**在使用本技能任何功能前，必须先执行以下初始化。**

将 Python 包安装到用户 site-packages，使 `wpsv7client` 和 `wps_credential_manager` 全局可用。

**Linux / macOS:**

```bash
python3 -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM" 2>/dev/null || pip3 install cryptography; USER_SITE=$(python3 -c "import site; print(site.getusersitepackages())"); mkdir -p "$USER_SITE"; PLUGIN_DIR=$(find ~/.claude/plugins/cache/wps365-marketplace/wps365 -maxdepth 4 -type d -name scripts 2>/dev/null | head -1); [ -n "$PLUGIN_DIR" ] && cp -a "$PLUGIN_DIR/wpsv7client" "$USER_SITE/" && cp -a "$PLUGIN_DIR/wps_credential_manager" "$USER_SITE/"; python3 -c "from wpsv7client import get_current_user; print('wps365 ready')"
```

**Windows PowerShell:**

```powershell
$USER_SITE = python -c "import site; print(site.getusersitepackages())"; if (-not (Test-Path $USER_SITE)) { New-Item -ItemType Directory -Path $USER_SITE -Force | Out-Null }; $PLUGIN_DIR = Get-ChildItem -Recurse -Directory -Filter scripts -ErrorAction SilentlyContinue "$env:USERPROFILE\.claude\plugins\cache\wps365-marketplace\wps365" | Select-Object -First 1 -ExpandProperty FullName; if ($PLUGIN_DIR) { Copy-Item -Recurse "$PLUGIN_DIR\wpsv7client" "$USER_SITE\"; Copy-Item -Recurse "$PLUGIN_DIR\wps_credential_manager" "$USER_SITE\" }; python -c "from wpsv7client import get_current_user; print('wps365 ready')"
```

看到 `wps365 ready` 后，**立即**执行凭证检查：

```bash
python -m wps_credential_manager status
```

如果显示"已配置"，说明已有凭证，可以继续使用该技能的其他功能。

如果显示"未配置"或"未找到凭证"，**先询问用户提供 app_id**：

> 首次使用 WPS 365 需要认证。请提供你的 WPS 365 企业应用 App ID（格式如 `AK20260501LJGRPT`），可在 WPS 365 管理后台 → 开放平台获取。

拿到 app_id 后执行：

```bash
python -m wps_credential_manager login --app-id <用户提供的app_id>
```

`login` 和 `refresh` 默认使用 cloud 模式（生成链接），不会受 localhost 回调问题影响。

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

```python
from wpsv7client import get_chat_list, list_chat_messages, send_message

resp = get_chat_list()
resp = send_message("chat_id", text="Hello")
resp = list_chat_messages("chat_id")
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
