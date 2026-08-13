---
description: Search WPS 365 enterprise contacts and resolve people for calendar, meeting, and messaging tasks.
argument-hint: [姓名、部门或联系人查询]
---

Use the WPS 365 Skill and unified CLI for the contact task below.

User request: $ARGUMENTS

Use `python -m wps365 contact user search <keyword>`.

If multiple people match, present minimal disambiguation details and ask the user to choose before using a person in a write operation. Do not expose unrelated contact information.