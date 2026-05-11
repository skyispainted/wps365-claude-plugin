---
name: wps365
description: WPS 365 V7 API 工具集。用于查询通讯录、管理日历日程、创建会议、操作云文档、管理多维表、发送聊天消息等企业协作任务。当用户提到通讯录、日程、会议、云文档、多维表、发消息、查人、创建文档等需求时使用。
---

# WPS 365 技能工具集

集成 WPS 365 V7 API，提供通讯录、日历、会议、云文档、多维表、IM 等企业协作能力。

## 认证

首次使用前需要认证，运行：

```bash
python -m wps_credential_manager login
```

浏览器完成登录后，`wps_sid` 会自动存储并在过期时无感刷新。

## 凭证管理

```bash
python -m wps_credential_manager status   # 查看当前凭证状态
python -m wps_credential_manager refresh  # 手动刷新 token
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
# 分页
resp = search_users("姓名", page_size=50, page_token=resp.get("page_token"))
```

### 日历

```python
from wpsv7client import list_calendars, list_events, create_event

# 列出所有日历
resp = list_calendars()
cals = resp["data"]["calendars"]

# 列出日程（须带时区）
resp = list_events("calendar_id",
    start_time="2026-05-11T09:00:00+08:00",
    end_time="2026-05-12T09:00:00+08:00")

# 创建日程
resp = create_event("calendar_id",
    start_time="2026-05-11T14:00:00+08:00",
    end_time="2026-05-11T15:00:00+08:00",
    summary="评审会议",
    attendee_user_ids=["user_id1", "user_id2"])
```

### 会议

```python
from wpsv7client import list_meetings, create_meeting

# 列出会议
resp = list_meetings()

# 创建会议
resp = create_meeting(
    subject="评审会议",
    start_time="2026-05-11T14:00:00+08:00",
    end_time="2026-05-11T15:00:00+08:00",
    participant_ids=["user_id1"])
```

### 云文档

```python
from wpsv7client import list_files, get_file

# 列出文件（默认个人云文档）
resp = list_files()
resp = list_files(drive_id="private", parent_id="root")

# 获取文件信息
resp = get_file(drive_id="private", file_id="xxx")
```

### 多维表

```python
from wpsv7client import (
    dbsheet_get_schema,
    dbsheet_list_records,
    dbsheet_batch_create_records,
)

# 获取表结构
resp = dbsheet_get_schema("file_id")

# 查询记录
resp = dbsheet_list_records("file_id", sheet_id=1)

# 批量创建记录
records = [{"fields": {"姓名": "张三", "部门": "研发"}}]
resp = dbsheet_batch_create_records("file_id", sheet_id=1, records=records)
```

### 即时消息

```python
from wpsv7client import get_chat_list, list_chat_messages, send_message

# 列出会话
resp = get_chat_list()

# 发送消息
resp = send_message("chat_id", text="Hello")

# 列出消息
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
