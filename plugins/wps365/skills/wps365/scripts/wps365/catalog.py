# -*- coding: utf-8 -*-
"""Single source of command discovery, risk, and help metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class CommandSpec:
    domain: str
    shortcut: str
    summary: str
    risk: str = "read"
    inputs: tuple[str, ...] = ()
    example: str = ""
    subcommand: tuple[str, ...] = ()
    legacy_only: bool = False

    @property
    def path(self) -> tuple[str, str]:
        return self.domain, self.shortcut

    @property
    def invocation(self) -> tuple[str, ...]:
        return (self.domain, *(self.subcommand or (self.shortcut,)))


def _command(
    domain: str,
    shortcut: str,
    summary: str,
    risk: str = "read",
    inputs: tuple[str, ...] = (),
    example: str = "",
    subcommand: tuple[str, ...] = (),
) -> CommandSpec:
    return CommandSpec(domain, shortcut, summary, risk, inputs, example, subcommand)


COMMANDS = (
    _command("contact", "+search", "按姓名搜索企业用户", inputs=("keyword",), example="contact +search 张三", subcommand=("user", "search")),
    _command("calendar", "+agenda", "查询指定时间段日程", inputs=("--start", "--end", "--calendar-id?"), subcommand=("event", "list")),
    _command("calendar", "+get", "查询日程详情", inputs=("--event-id", "--calendar-id?"), subcommand=("event", "get")),
    _command("calendar", "+create", "创建日程", "write", ("--start", "--end", "--title?", "--calendar-id?"), subcommand=("event", "create")),
    _command("calendar", "+update", "更新日程", "write", ("--event-id", "至少一个更新字段", "--calendar-id?"), subcommand=("event", "update")),
    _command("calendar", "+delete", "删除日程", "high-risk-write", ("--event-id", "--calendar-id?"), subcommand=("event", "delete")),
    _command("calendar", "+freebusy", "查询用户或会议室忙闲", inputs=("--start", "--end", "--user-ids|--room-ids"), subcommand=("availability", "list")),
    _command("calendar", "+calendar-list", "列出日历", inputs=("--page-size?", "--page-token?"), subcommand=("calendar", "list")),
    _command("calendar", "+calendar-get", "查看日历", inputs=("calendar_id",), subcommand=("calendar", "get")),
    _command("calendar", "+calendar-create", "创建日历", "write", ("--title", "--color", "--desc?"), subcommand=("calendar", "create")),
    _command("calendar", "+calendar-update", "更新日历", "write", ("calendar_id", "至少一个更新字段"), subcommand=("calendar", "update")),
    _command("calendar", "+calendar-delete", "删除日历", "high-risk-write", ("calendar_id",), subcommand=("calendar", "delete")),
    _command("meeting", "+list", "查询预约会议", inputs=("--start?", "--end?"), subcommand=("meeting", "list")),
    _command("meeting", "+get", "查询会议详情", inputs=("--meeting-id",), subcommand=("meeting", "get")),
    _command("meeting", "+create", "创建预约会议", "write", ("--subject", "--start", "--end"), subcommand=("meeting", "create")),
    _command("meeting", "+update", "更新预约会议", "write", ("--meeting-id", "至少一个更新字段"), subcommand=("meeting", "update")),
    _command("meeting", "+cancel", "取消预约会议", "high-risk-write", ("--meeting-id",), subcommand=("meeting", "cancel")),
    _command("meeting", "+participants", "查看、添加或移除参会人", "write", ("--meeting-id", "--action list|add|remove", "--ids?")),
    _command("meeting", "+participant-list", "查看参会人", inputs=("--meeting-id",), subcommand=("participant", "list")),
    _command("meeting", "+participant-add", "添加参会人", "write", ("--meeting-id", "--ids"), subcommand=("participant", "add")),
    _command("meeting", "+participant-remove", "移除参会人", "write", ("--meeting-id", "--ids"), subcommand=("participant", "remove")),
    _command("meeting", "+room-level-list", "列出会议室层级", inputs=("--room-level-id?", "--page-size?"), subcommand=("room-level", "list")),
    _command("meeting", "+event-room-list", "列出日程会议室", inputs=("--calendar-id", "--event-id"), subcommand=("event-room", "list")),
    _command("meeting", "+started-list", "列出已开始会议", inputs=("--start", "--end", "--page-size?"), subcommand=("started", "list")),
    _command("meeting", "+recording-list", "列出会议录制", inputs=("--meeting-id",), subcommand=("recording", "list")),
    _command("meeting", "+recording-summary", "读取录制摘要", inputs=("--meeting-id", "--recording-id"), subcommand=("recording", "summary")),
    _command("meeting", "+recording-transcript", "读取录制转写", inputs=("--meeting-id", "--recording-id"), subcommand=("recording", "transcript")),
    _command("meeting", "+minute-list", "列出会议纪要", inputs=("--meeting-id",), subcommand=("minute", "list")),
    _command("meeting", "+minute-summary", "读取纪要摘要", inputs=("--meeting-id", "--minute-id"), subcommand=("minute", "summary")),
    _command("meeting", "+minute-transcript", "读取纪要转写", inputs=("--meeting-id", "--minute-id"), subcommand=("minute", "transcript")),
    _command("meeting", "+artifact-export", "批量导出会议录制或纪要工件", "write", ("--meeting-id", "--kind recordings|minutes", "--output-dir", "--include?"), subcommand=("artifact", "export")),
    _command("drive", "+list", "列出云盘目录", inputs=("--drive?", "--parent?"), subcommand=("directory", "list")),
    _command("drive", "+search", "搜索云文档并返回可复用 read_args", inputs=("keyword",), subcommand=("file", "search")),
    _command("drive", "+get", "获取文件详情", inputs=("file_id 或 --link-id <link_id>",), subcommand=("file", "get")),
    _command("drive", "+read", "读取云文档正文", inputs=("file_id 或 --link-id <link_id>", "--format?"), subcommand=("file", "read")),
    _command("drive", "+create", "创建文件、文件夹或快捷方式", "write", ("name", "--file-type?", "--drive?"), subcommand=("file", "create")),
    _command("drive", "+upload", "上传本地文件", "write", ("file_path", "--drive?", "--parent?"), subcommand=("file", "upload")),
    _command("drive", "+write", "写入智能文档 Markdown", "write", ("file_id", "--content", "--title?"), subcommand=("file", "write")),
    _command("drive", "+overwrite", "覆盖非 .otl 文档的新版本", "high-risk-write", ("--file-id", "--source", "--drive?"), subcommand=("file", "overwrite")),
    _command("drive", "+convert-overwrite", "转换 Markdown 后覆盖文档", "high-risk-write", ("--file-id", "--content|--source", "--format docx|pdf", "--drive?"), subcommand=("file", "convert-overwrite")),
    _command("drive", "+copy", "复制云文档", "write", ("--file-id", "--dst-parent-id", "--drive?", "--dst-drive-id?"), subcommand=("file", "copy")),
    _command("drive", "+move", "移动云文档", "high-risk-write", ("--file-id", "--dst-parent-id", "--drive?", "--dst-drive-id?"), subcommand=("file", "move")),
    _command("drive", "+rename", "重命名云文档", "write", ("--file-id", "--name", "--drive?"), subcommand=("file", "rename")),
    _command("drive", "+share", "开启文件分享", "high-risk-write", ("--file-id", "--drive?"), subcommand=("file", "share")),
    _command("drive", "+unshare", "关闭文件分享", "high-risk-write", ("--file-id", "--drive?"), subcommand=("file", "unshare")),
    _command("drive", "+restore", "还原回收站文件", "write", ("--file-id",), subcommand=("trash", "restore")),
    _command("drive", "+recent", "列出最近文档", inputs=("--page-size?", "--page-token?"), subcommand=("recent", "list")),
    _command("drive", "+favorite-list", "列出收藏文档", inputs=("--page-size?", "--page-token?"), subcommand=("favorite", "list")),
    _command("drive", "+favorite-add", "添加收藏文档", "write", ("file_ids",), subcommand=("favorite", "add")),
    _command("drive", "+favorite-remove", "移除收藏文档", "write", ("file_ids",), subcommand=("favorite", "remove")),
    _command("drive", "+trash-list", "列出回收站文档", inputs=("--drive?", "--page-size?"), subcommand=("trash", "list")),
    _command("drive", "+download-url", "获取临时下载地址", inputs=("--file-id", "--drive?"), subcommand=("download-url", "get")),
    _command("drive", "+name-check", "检查目录下文件名是否存在", inputs=("name", "--parent?", "--drive?"), subcommand=("name", "check")),
    _command("drive", "+label-list", "列出文档标签", inputs=("--page-size?",), subcommand=("label", "list")),
    _command("drive", "+label-get", "查看文档标签", inputs=("label_id",), subcommand=("label", "get")),
    _command("drive", "+label-create", "创建文档标签", "write", ("name",), subcommand=("label", "create")),
    _command("drive", "+label-object-list", "列出标签下文档", inputs=("label_id",), subcommand=("label", "object-list")),
    _command("drive", "+label-add", "为文档添加标签", "write", ("label_id", "file_ids"), subcommand=("label", "add")),
    _command("drive", "+label-remove", "从文档移除标签", "write", ("label_id", "file_ids"), subcommand=("label", "remove")),
    _command("base", "+schema", "读取多维表结构", inputs=("file_id",), subcommand=("schema", "get")),
    _command("base", "+list", "列出多维表记录", inputs=("file_id", "sheet_id", "--page-size?", "--page-token?", "--filter?"), subcommand=("record", "list")),
    _command("base", "+get", "读取一条多维表记录", inputs=("file_id", "sheet_id", "record_id"), subcommand=("record", "get")),
    _command("base", "+search", "按记录 ID 查询多维表记录", inputs=("file_id", "sheet_id", "record_ids"), subcommand=("record", "search")),
    _command("base", "+create", "创建多维表记录", "write", ("file_id", "sheet_id", "--json"), subcommand=("record", "create")),
    _command("base", "+update", "更新多维表记录", "write", ("file_id", "sheet_id", "--json"), subcommand=("record", "update")),
    _command("base", "+delete", "删除多维表记录", "high-risk-write", ("file_id", "sheet_id", "record_ids"), subcommand=("record", "delete")),
    _command("base", "+sheet-create", "创建数据表", "write", ("file_id", "--name?", "--fields?", "--views?"), subcommand=("sheet", "create")),
    _command("base", "+sheet-update", "更新数据表", "write", ("file_id", "sheet_id", "--name"), subcommand=("sheet", "update")),
    _command("base", "+sheet-delete", "删除数据表", "high-risk-write", ("file_id", "sheet_id"), subcommand=("sheet", "delete")),
    _command("base", "+view-create", "创建数据表视图", "write", ("file_id", "sheet_id", "--name?", "--type?"), subcommand=("view", "create")),
    _command("base", "+form-get", "查看表单视图元数据", inputs=("file_id", "sheet_id", "view_id"), subcommand=("form", "get")),
    _command("base", "+form-update", "更新表单视图元数据", "write", ("file_id", "sheet_id", "view_id", "--name?|--desc?"), subcommand=("form", "update")),
    _command("im", "+list", "列出会话", inputs=("--page-size?",), subcommand=("chat", "list")),
    _command("im", "+get", "读取会话详情", inputs=("chat_id",), subcommand=("chat", "get")),
    _command("im", "+search", "搜索会话", inputs=("keyword",), subcommand=("chat", "search")),
    _command("im", "+history", "读取会话历史", inputs=("chat_id",), subcommand=("message", "history")),
    _command("im", "+send", "发送文本消息", "write", ("chat_id", "text"), subcommand=("message", "send")),
    _command("im", "+send-rich", "发送富文本消息", "write", ("chat_id", "--json"), subcommand=("message", "send-rich")),
    _command("im", "+send-image", "发送图片消息", "write", ("chat_id", "--json"), subcommand=("message", "send-image")),
    _command("im", "+send-file", "发送文件或云文档消息", "write", ("chat_id", "--json"), subcommand=("message", "send-file")),
    _command("im", "+send-card", "发送卡片消息", "write", ("chat_id", "--json"), subcommand=("message", "send-card")),
    _command("im", "+recall", "撤回消息", "high-risk-write", ("chat_id", "message_id"), subcommand=("message", "recall")),
    _command("im", "+recent", "列出最近会话", inputs=("--page-size?", "--unread?", "--mention-me?"), subcommand=("recent", "list")),
    _command("im", "+message-search", "全局搜索消息", inputs=("keyword?", "--chat-ids?|--start?|--end?"), subcommand=("message", "search")),
)


BY_PATH = {spec.path: spec for spec in COMMANDS}
BY_SUBCOMMAND = {(spec.domain, *spec.subcommand): spec for spec in COMMANDS if spec.subcommand}


def resolve(domain: str, arguments: Sequence[str]) -> tuple[CommandSpec, int] | None:
    if arguments and arguments[0].startswith("+"):
        spec = BY_PATH.get((domain, arguments[0]))
        return (spec, 1) if spec else None
    for length in range(min(3, len(arguments)), 0, -1):
        spec = BY_SUBCOMMAND.get((domain, *arguments[:length]))
        if spec:
            return spec, length
    return None


def schema(domain: str | None = None, *path: str) -> dict:
    specs = COMMANDS
    if domain:
        specs = tuple(spec for spec in specs if spec.domain == domain)
        if not specs:
            raise ValueError(f"未知命令域: {domain}")
    if path:
        requested = tuple(path)
        specs = tuple(spec for spec in specs if spec.shortcut == requested[0] or spec.subcommand == requested)
        if not specs:
            raise ValueError(f"未知命令: {' '.join((domain or '', *requested)).strip()}")
    return {
        "domains": sorted({spec.domain for spec in COMMANDS}),
        "commands": [
            {
                "domain": spec.domain,
                "shortcut": spec.shortcut,
                "subcommand": list(spec.subcommand),
                "invocation": " ".join(spec.invocation),
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
