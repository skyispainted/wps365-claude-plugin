---
name: wps365
description: WPS 365 V7 API 工具集。用于查询通讯录、管理日历日程、创建会议、操作云文档、管理多维表、发送聊天消息等企业协作任务。当用户提到通讯录、日程、会议、云文档、多维表、发消息、查人、创建文档等需求时使用。
---

# WPS 365 技能工具集

集成 WPS 365 V7 API，提供通讯录、日历、会议、云文档、多维表、IM 等企业协作能力。

## 认证

首次使用前需要认证，运行：

```bash
python -m wps_credential_manager login --flow cloud
```

浏览器中完成登录后，`wps_sid` 会自动存储并在过期时无感刷新。

## 凭证管理

```bash
python -m wps_credential_manager status   # 查看当前凭证状态
python -m wps_credential_manager refresh  # 手动刷新 token
python -m wps_credential_manager logout   # 清除凭证（重新登录）
python -m wps_credential_manager test     # 测试凭证是否有效
```

## Python API

所有模块通过 `from wpsv7client import ...` 导入：

### 当前用户
```python
from wpsv7client import get_current_user
info = get_current_user()
```

### 通讯录
```python
from wpsv7client.contacts import search_users, get_user
users = search_users("姓名")           # 按姓名搜索
dept_users = search_users("", dept_id="123")  # 按部门查询
user = get_user("user_id")            # 获取用户详情
```

### 日历
```python
from wpsv7client.calendar import list_calendars, list_events, create_event
cals = list_calendars()                        # 列出日历
events = list_events("calendar_id",             # 列出日程
    start_time="2026-05-11T09:00:00+08:00",
    end_time="2026-05-12T09:00:00+08:00")
event = create_event("calendar_id",             # 创建日程
    title="会议",
    start_time="2026-05-11T14:00:00+08:00",
    end_time="2026-05-11T15:00:00+08:00",
    attendees=["user_id1", "user_id2"])
```

### 会议
```python
from wpsv7client.meeting import list_meetings, create_meeting
meetings = list_meetings()                      # 列出会议
meeting = create_meeting(                       # 创建会议
    title="评审会议",
    start_time="2026-05-11T14:00:00+08:00",
    end_time="2026-05-11T15:00:00+08:00",
    attendees=["user_id1"])
```

### 云文档
```python
from wpsv7client.drive import list_files, get_file_info
files = list_files(folder_id="root")            # 列出文件
info = get_file_info("file_id")                 # 获取文件信息
```

### 多维表
```python
from wpsv7client.dbsheet import get_schema, query_records, create_record
schema = get_schema("file_id")                  # 获取表结构
records = query_records("file_id", "table_id")  # 查询记录
create_record("file_id", "table_id", {...})     # 创建记录
```

### 即时消息
```python
from wpsv7client.im import list_conversations, send_message
convs = list_conversations()                    # 列出会话
send_message("chat_id", "Hello")               # 发送消息
```

## 时间格式

所有时间参数必须带时区：
- `2026-05-11T09:00:00+08:00`（东八区）
- `2026-05-11T01:00:00Z`（UTC）

禁止使用无时区格式如 `2026-05-11T09:00:00`。

## 错误处理

如果 API 返回认证错误（401 / csrfCheckFailed / NOT_LOGIN），自动刷新凭证后重试。
如果刷新失败，提示用户重新运行 `python -m wps_credential_manager login`。
