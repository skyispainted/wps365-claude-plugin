---
description: WPS 联系人 / 协作联系人 / 企业通讯录：按姓名或部门搜索人员，为日程、会议和消息操作解析成员。以上名称含义相同。
argument-hint: [例如：搜索协作联系人张三、查找某部门成员]
---

Use the WPS 365 Skill and unified CLI for the contact task below.

User request: $ARGUMENTS

Use `wps365 contact +search <keyword>`.

If multiple people match, present minimal disambiguation details and ask the user to choose before using a person in a write operation. Do not expose unrelated contact information.