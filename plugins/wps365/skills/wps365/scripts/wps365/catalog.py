# -*- coding: utf-8 -*-
"""Single source of command discovery, risk, and help metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    domain: str
    shortcut: str
    summary: str
    risk: str = "read"
    inputs: tuple[str, ...] = ()
    example: str = ""
    legacy_only: bool = False

    @property
    def path(self) -> tuple[str, str]:
        return self.domain, self.shortcut


COMMANDS = (
    CommandSpec("contact", "+search", "按姓名搜索企业用户", inputs=("keyword",), example="contact +search 张三"),
    CommandSpec("calendar", "+agenda", "查询指定时间段日程", inputs=("--start", "--end", "--calendar-id?")),
    CommandSpec("calendar", "+get", "查询日程详情", inputs=("--event-id", "--calendar-id?")),
    CommandSpec("calendar", "+create", "创建日程", "write", ("--start", "--end", "--title?", "--calendar-id?")),
    CommandSpec("calendar", "+update", "更新日程", "write", ("--event-id", "至少一个更新字段", "--calendar-id?")),
    CommandSpec("calendar", "+delete", "删除日程", "high-risk-write", ("--event-id", "--calendar-id?")),
    CommandSpec("calendar", "+freebusy", "查询用户或会议室忙闲", inputs=("--start", "--end", "--user-ids|--room-ids")),
    CommandSpec("meeting", "+list", "查询会议", inputs=("--start?", "--end?")),
    CommandSpec("meeting", "+get", "查询会议详情", inputs=("--meeting-id",)),
    CommandSpec("meeting", "+create", "创建预约会议", "write", ("--subject", "--start", "--end")),
    CommandSpec("meeting", "+update", "更新预约会议", "write", ("--meeting-id", "至少一个更新字段")),
    CommandSpec("meeting", "+cancel", "取消预约会议", "high-risk-write", ("--meeting-id",)),
    CommandSpec("meeting", "+participants", "查看、添加或移除参会人", "write", ("--meeting-id", "--action list|add|remove", "--ids?")),
    CommandSpec("drive", "+list", "列出云盘目录", inputs=("--drive?", "--parent?")),
    CommandSpec("drive", "+search", "搜索云文档", inputs=("keyword",)),
    CommandSpec("drive", "+get", "获取文件详情", inputs=("file_id 或 --link-id",)),
    CommandSpec("drive", "+read", "读取云文档正文", inputs=("file_id 或 --link-id", "--format?")),
    CommandSpec("drive", "+create", "创建文件、文件夹或快捷方式", "write", ("name", "--file-type?", "--drive?")),
    CommandSpec("drive", "+upload", "上传本地文件", "write", ("file_path", "--drive?", "--parent?")),
    CommandSpec("drive", "+write", "写入智能文档 Markdown", "write", ("file_id", "--content", "--title?")),
    CommandSpec("drive", "+copy", "复制云文档", "write", ("--file-id", "--dst-parent-id", "--drive?", "--dst-drive-id?")),
    CommandSpec("drive", "+move", "移动云文档", "high-risk-write", ("--file-id", "--dst-parent-id", "--drive?", "--dst-drive-id?")),
    CommandSpec("drive", "+rename", "重命名云文档", "write", ("--file-id", "--name", "--drive?")),
    CommandSpec("drive", "+share", "开启文件分享", "high-risk-write", ("--file-id", "--drive?")),
    CommandSpec("drive", "+unshare", "关闭文件分享", "high-risk-write", ("--file-id", "--drive?")),
    CommandSpec("drive", "+restore", "还原回收站文件", "write", ("--file-id",)),
    CommandSpec("base", "+schema", "读取多维表结构", inputs=("file_id",)),
    CommandSpec("base", "+list", "列出多维表记录", inputs=("file_id", "sheet_id")),
    CommandSpec("base", "+get", "读取一条多维表记录", inputs=("file_id", "sheet_id", "record_id")),
    CommandSpec("base", "+search", "按记录 ID 查询多维表记录", inputs=("file_id", "sheet_id", "record_ids")),
    CommandSpec("base", "+create", "创建多维表记录", "write", ("file_id", "sheet_id", "--json")),
    CommandSpec("base", "+update", "更新多维表记录", "write", ("file_id", "sheet_id", "--json")),
    CommandSpec("base", "+delete", "删除多维表记录", "high-risk-write", ("file_id", "sheet_id", "record_ids")),
    CommandSpec("im", "+list", "列出会话", inputs=("--page-size?",)),
    CommandSpec("im", "+get", "读取会话详情", inputs=("chat_id",)),
    CommandSpec("im", "+search", "搜索会话", inputs=("keyword",)),
    CommandSpec("im", "+history", "读取会话历史", inputs=("chat_id",)),
    CommandSpec("im", "+send", "发送消息", "write", ("chat_id", "text")),
    CommandSpec("im", "+recall", "撤回消息", "high-risk-write", ("chat_id", "message_id")),
)


BY_PATH = {spec.path: spec for spec in COMMANDS}


def schema(domain: str | None = None, shortcut: str | None = None) -> dict:
    specs = COMMANDS
    if domain:
        specs = tuple(spec for spec in specs if spec.domain == domain)
        if not specs:
            raise ValueError(f"未知命令域: {domain}")
    if shortcut:
        specs = tuple(spec for spec in specs if spec.shortcut == shortcut)
        if not specs:
            raise ValueError(f"未知快捷命令: {domain} {shortcut}")
    return {
        "domains": sorted({spec.domain for spec in COMMANDS}),
        "commands": [
            {
                "domain": spec.domain,
                "shortcut": spec.shortcut,
                "summary": spec.summary,
                "risk": spec.risk,
                "requires_confirmation": spec.risk == "high-risk-write",
                "inputs": list(spec.inputs),
                "example": spec.example,
                "legacy_only": spec.legacy_only,
            }
            for spec in specs
        ],
    }
