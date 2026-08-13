# -*- coding: utf-8 -*-
"""Direct, agent-oriented handlers built on the existing WPS client package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Sequence

import wpsv7client as wps
from wps_credential_manager import manager

from .errors import WpsCliError, from_response, validation


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser(prog: str) -> ArgumentParser:
    return ArgumentParser(prog=f"python -m wps365 {prog}", add_help=False)


def _parse(parser: ArgumentParser, arguments: Sequence[str]):
    try:
        return parser.parse_args(arguments)
    except SystemExit as error:
        raise validation("命令参数无效", "运行 `python -m wps365 schema <domain> <shortcut>` 查看输入契约。") from error


def _response(response: dict) -> dict:
    error = from_response(response)
    if error:
        raise error
    return response.get("data") if isinstance(response, dict) and response.get("data") is not None else {}


def _csv(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _json(value: str, name: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise validation(f"{name} 必须是合法 JSON") from error


def _drive_id(value: str | None) -> str:
    return wps.get_drive_id(value or "private")


def _credential_status() -> dict:
    raw = manager.status()
    return {
        "configured": bool(raw.get("configured")),
        "app_id_configured": bool(raw.get("app_id")),
        "env_sid": bool(raw.get("env_sid")),
        "user": {
            "nickname": raw.get("nickname"),
            "user_id": raw.get("user_id"),
        } if raw.get("configured") else None,
        "created_at": raw.get("created_at"),
        "last_used_at": raw.get("last_used_at"),
    }


def _resolve_link(link_id: str, drive: str | None) -> tuple[str, str]:
    response = wps.get_link_meta(link_id)
    data = _response(response)
    if not data.get("file_id"):
        raise validation("分享链接未返回 file_id")
    return str(data["file_id"]), str(data.get("drive_id") or _drive_id(drive))


def auth(arguments: Sequence[str]) -> dict:
    parser = _parser("auth")
    sub = parser.add_subparsers(dest="action", required=True)
    status = sub.add_parser("status")
    status.add_argument("--verify", action="store_true")
    login = sub.add_parser("login")
    login.add_argument("--app-id", default="")
    login.add_argument("--flow", choices=("local", "cloud"), default="local")
    refresh = sub.add_parser("refresh")
    refresh.add_argument("--flow", choices=("local", "cloud"), default="local")
    sub.add_parser("logout")
    sub.add_parser("test")
    args = _parse(parser, arguments)

    if args.action == "status":
        data = _credential_status()
        if args.verify:
            check = manager.test_sid()
            data = {**data, "verified": bool(check.get("valid")), "user": check.get("user") if check.get("valid") else None}
        return data
    if args.action == "login":
        if not args.app_id:
            stored = manager.status().get("app_id") or ""
            if not stored:
                raise validation("缺少 WPS 365 数字员工 App ID", "向用户询问 App ID 后重试 `wps365 auth login --app-id <app_id>`。")
            args.app_id = stored
        result = manager.login(app_id=args.app_id, flow=args.flow)
        check = manager.test_sid()
        if not check.get("valid"):
            raise WpsCliError(check.get("error") or "登录后凭证验证失败", "authentication", "credentials_invalid")
        return {"user": {"nickname": result.get("nickname"), "user_id": result.get("user_id")}, "verified": True}
    if args.action == "refresh":
        result = manager.refresh(flow=args.flow)
        return {"user": {"nickname": result.get("nickname"), "user_id": result.get("user_id")}}
    if args.action == "logout":
        manager.logout()
        return {"logged_out": True}
    check = manager.test_sid()
    if not check.get("valid"):
        raise WpsCliError(check.get("error") or "sid 无效", "authentication", "credentials_invalid")
    return {"valid": True, "user": check.get("user") or {}}


def config(arguments: Sequence[str]) -> dict:
    parser = _parser("config")
    parser.add_argument("action", nargs="?", default="status", choices=("status", "doctor"))
    args = _parse(parser, arguments)
    state = _credential_status()
    if args.action == "status":
        return state
    try:
        check = manager.test_sid()
    except Exception as error:
        raise WpsCliError(str(error), "authentication", "credentials_missing") from error
    if not check.get("valid"):
        raise WpsCliError(check.get("error") or "凭证不可用", "authentication", "credentials_invalid")
    return {"python_package": True, "credentials": state, "verified": True, "user": check.get("user") or {}}


def whoami(arguments: Sequence[str]) -> dict:
    if arguments:
        raise validation("whoami 不接受参数")
    return _response(wps.get_current_user())


def contact(shortcut: str, arguments: Sequence[str]) -> dict:
    if shortcut != "+search":
        raise validation(f"未知 contact 快捷命令: {shortcut}")
    parser = _parser("contact +search")
    parser.add_argument("keyword")
    args = _parse(parser, arguments)
    return _response(wps.search_users(args.keyword))


def calendar(shortcut: str, arguments: Sequence[str]) -> dict:
    parser = _parser(f"calendar {shortcut}")
    parser.add_argument("--calendar-id", default="primary")
    if shortcut == "+agenda":
        parser.add_argument("--start", required=True)
        parser.add_argument("--end", required=True)
        args = _parse(parser, arguments)
        return _response(wps.list_events(args.calendar_id, args.start, args.end))
    if shortcut == "+get":
        parser.add_argument("--event-id", required=True)
        args = _parse(parser, arguments)
        return _response(wps.get_event(args.calendar_id, args.event_id))
    if shortcut == "+create":
        parser.add_argument("--start", required=True)
        parser.add_argument("--end", required=True)
        parser.add_argument("--title")
        parser.add_argument("--desc")
        parser.add_argument("--location")
        parser.add_argument("--attendees")
        args = _parse(parser, arguments)
        return _response(wps.create_event(args.calendar_id, args.start, args.end, summary=args.title, description=args.desc, location=args.location, attendee_user_ids=_csv(args.attendees)))
    if shortcut == "+update":
        parser.add_argument("--event-id", required=True)
        parser.add_argument("--title")
        parser.add_argument("--desc")
        parser.add_argument("--start")
        parser.add_argument("--end")
        parser.add_argument("--location")
        parser.add_argument("--attendees")
        parser.add_argument("--remove-attendees")
        args = _parse(parser, arguments)
        if not any((args.title, args.desc, args.start, args.end, args.location, args.attendees, args.remove_attendees)):
            raise validation("请至少提供一个更新字段")
        response = wps.update_event(args.calendar_id, args.event_id, summary=args.title, description=args.desc, start_time=args.start, end_time=args.end, location=args.location)
        result = _response(response)
        if args.attendees:
            _response(wps.batch_create_event_attendees(args.calendar_id, args.event_id, _csv(args.attendees)))
        if args.remove_attendees:
            _response(wps.batch_delete_event_attendees(args.calendar_id, args.event_id, _csv(args.remove_attendees)))
        return result
    if shortcut == "+delete":
        parser.add_argument("--event-id", required=True)
        args = _parse(parser, arguments)
        return _response(wps.delete_event(args.calendar_id, args.event_id))
    if shortcut == "+freebusy":
        parser.add_argument("--start", required=True)
        parser.add_argument("--end", required=True)
        parser.add_argument("--user-ids")
        parser.add_argument("--room-ids")
        args = _parse(parser, arguments)
        users, rooms = _csv(args.user_ids), _csv(args.room_ids)
        if not users and not rooms:
            raise validation("请提供 --user-ids 或 --room-ids")
        return _response(wps.list_free_busy(args.start, args.end, user_ids=users, room_ids=rooms))
    raise validation(f"未知 calendar 快捷命令: {shortcut}")


def meeting(shortcut: str, arguments: Sequence[str]) -> dict:
    parser = _parser(f"meeting {shortcut}")
    if shortcut == "+list":
        parser.add_argument("--start")
        parser.add_argument("--end")
        args = _parse(parser, arguments)
        return _response(wps.list_meetings(args.start, args.end))
    if shortcut == "+get":
        parser.add_argument("--meeting-id", required=True)
        args = _parse(parser, arguments)
        return _response(wps.get_meeting(args.meeting_id))
    if shortcut == "+create":
        parser.add_argument("--subject", required=True)
        parser.add_argument("--start", required=True)
        parser.add_argument("--end", required=True)
        parser.add_argument("--participants")
        parser.add_argument("--join-permission", choices=("anyone", "company_users", "only_invitee"))
        args = _parse(parser, arguments)
        return _response(wps.create_meeting(args.subject, args.start, args.end, participant_ids=_csv(args.participants), allow_attendee_to_join=args.join_permission))
    if shortcut == "+update":
        parser.add_argument("--meeting-id", required=True)
        parser.add_argument("--subject")
        parser.add_argument("--start")
        parser.add_argument("--end")
        parser.add_argument("--join-permission", choices=("anyone", "company_users", "only_invitee"))
        args = _parse(parser, arguments)
        return _response(wps.update_meeting(args.meeting_id, subject=args.subject, start_time=args.start, end_time=args.end, allow_attendee_to_join=args.join_permission))
    if shortcut == "+cancel":
        parser.add_argument("--meeting-id", required=True)
        args = _parse(parser, arguments)
        return _response(wps.delete_meeting(args.meeting_id))
    if shortcut == "+participants":
        parser.add_argument("--meeting-id", required=True)
        parser.add_argument("--action", choices=("list", "add", "remove"), default="list")
        parser.add_argument("--ids")
        args = _parse(parser, arguments)
        if args.action == "list":
            return _response(wps.list_meeting_participants(args.meeting_id))
        ids = _csv(args.ids)
        if not ids:
            raise validation("添加或移除参会人时请提供 --ids")
        function = wps.put_meeting_participants if args.action == "add" else wps.delete_meeting_participants
        return _response(function(args.meeting_id, ids))
    raise validation(f"未知 meeting 快捷命令: {shortcut}")


def drive(shortcut: str, arguments: Sequence[str]) -> dict:
    parser = _parser(f"drive {shortcut}")
    if shortcut == "+list":
        parser.add_argument("--drive", default="private")
        parser.add_argument("--parent", default="root")
        parser.add_argument("--page-size", type=int, default=50)
        args = _parse(parser, arguments)
        return _response(wps.list_files(_drive_id(args.drive), args.parent, args.page_size))
    if shortcut == "+search":
        parser.add_argument("keyword")
        parser.add_argument("--type", choices=("file_name", "content", "all"), default="all")
        args = _parse(parser, arguments)
        return _response(wps.search_files(args.keyword, search_type=args.type))
    if shortcut in ("+get", "+read"):
        parser.add_argument("file_id", nargs="?")
        parser.add_argument("--link-id")
        parser.add_argument("--drive", default="private")
        parser.add_argument("--format", choices=("plain", "markdown", "html", "kdc"), default="markdown")
        args = _parse(parser, arguments)
        if bool(args.file_id) == bool(args.link_id):
            raise validation("请提供 file_id，或使用 --link-id 提供分享链接 ID（二者只能选一个）")
        file_id, drive_id = (args.file_id, _drive_id(args.drive)) if args.file_id else _resolve_link(args.link_id, args.drive)
        if shortcut == "+get":
            return _response(wps.get_file(drive_id, file_id))
        return _response(wps.get_file_content_extract(drive_id, file_id, format=args.format))
    if shortcut == "+create":
        parser.add_argument("name")
        parser.add_argument("--drive", default="private")
        parser.add_argument("--parent-id", default="0")
        parser.add_argument("--file-type", choices=("file", "folder", "shortcut"), default="file")
        parser.add_argument("--file-id")
        args = _parse(parser, arguments)
        return _response(wps.create_file(_drive_id(args.drive), args.name, parent_id=args.parent_id, file_type=args.file_type, file_id=args.file_id))
    if shortcut == "+upload":
        parser.add_argument("file_path")
        parser.add_argument("--drive", default="private")
        parser.add_argument("--parent", default="root")
        parser.add_argument("--filename")
        args = _parse(parser, arguments)
        if not Path(args.file_path).is_file():
            raise validation(f"文件不存在: {args.file_path}")
        return _response(wps.upload_simple(args.file_path, _drive_id(args.drive), parent_id=args.parent, file_name=args.filename))
    if shortcut == "+write":
        parser.add_argument("file_id")
        parser.add_argument("--content", required=True)
        parser.add_argument("--title")
        args = _parse(parser, arguments)
        response = wps.get_file_directly(args.file_id)
        data = _response(response)
        name = str(data.get("name") or "").lower()
        if not name.endswith(".otl"):
            raise validation("统一写入当前仅支持智能文档 (.otl)", "其它格式请使用 `wps365 legacy drive write`。")
        wps.write_airpage_content(args.file_id, args.title or data.get("name") or "文档", args.content, pos="begin")
        return {"file_id": args.file_id, "written": True}
    if shortcut in ("+copy", "+move"):
        parser.add_argument("--file-id", required=True)
        parser.add_argument("--drive", default="private")
        parser.add_argument("--dst-drive-id")
        parser.add_argument("--dst-parent-id", required=True)
        args = _parse(parser, arguments)
        source = _drive_id(args.drive)
        destination = args.dst_drive_id or source
        function = wps.copy_file if shortcut == "+copy" else wps.move_file
        return _response(function(source, args.file_id, destination, args.dst_parent_id))
    if shortcut == "+rename":
        parser.add_argument("--file-id", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--drive", default="private")
        args = _parse(parser, arguments)
        return _response(wps.rename_file(_drive_id(args.drive), args.file_id, args.name))
    if shortcut in ("+share", "+unshare"):
        parser.add_argument("--file-id", required=True)
        parser.add_argument("--drive", default="private")
        parser.add_argument("--scope")
        args = _parse(parser, arguments)
        drive_id = _drive_id(args.drive)
        if shortcut == "+share":
            return _response(wps.open_file_link(drive_id, args.file_id, scope=args.scope))
        return _response(wps.close_file_link(drive_id, args.file_id))
    if shortcut == "+restore":
        parser.add_argument("--file-id", required=True)
        args = _parse(parser, arguments)
        return _response(wps.restore_deleted_file(args.file_id))
    raise validation(f"未知 drive 快捷命令: {shortcut}")


def base(shortcut: str, arguments: Sequence[str]) -> dict:
    parser = _parser(f"base {shortcut}")
    parser.add_argument("file_id")
    if shortcut == "+schema":
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_get_schema(args.file_id))
    parser.add_argument("sheet_id", type=int)
    if shortcut == "+list":
        parser.add_argument("--page-size", type=int)
        parser.add_argument("--filter")
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_list_records(args.file_id, args.sheet_id, page_size=args.page_size, filter_body=_json(args.filter, "--filter") if args.filter else None))
    if shortcut == "+get":
        parser.add_argument("record_id")
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_get_record(args.file_id, args.sheet_id, args.record_id))
    if shortcut == "+search":
        parser.add_argument("record_ids", nargs="+")
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_search_records(args.file_id, args.sheet_id, args.record_ids))
    if shortcut in ("+create", "+update"):
        parser.add_argument("--json", required=True)
        args = _parse(parser, arguments)
        records = _json(args.json, "--json")
        if not isinstance(records, list):
            raise validation("--json 必须是记录数组")
        function = wps.dbsheet_batch_create_records if shortcut == "+create" else wps.dbsheet_batch_update_records
        return _response(function(args.file_id, args.sheet_id, records))
    if shortcut == "+delete":
        parser.add_argument("record_ids", nargs="+")
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_batch_delete_records(args.file_id, args.sheet_id, args.record_ids))
    raise validation(f"未知 base 快捷命令: {shortcut}")


def im(shortcut: str, arguments: Sequence[str]) -> dict:
    parser = _parser(f"im {shortcut}")
    if shortcut == "+list":
        parser.add_argument("--page-size", type=int, default=50)
        args = _parse(parser, arguments)
        return _response(wps.get_chat_list(page_size=args.page_size))
    if shortcut == "+get":
        parser.add_argument("chat_id")
        args = _parse(parser, arguments)
        return _response(wps.get_chat(args.chat_id))
    if shortcut == "+search":
        parser.add_argument("keyword")
        args = _parse(parser, arguments)
        return _response(wps.search_chats(args.keyword, with_total=True))
    if shortcut == "+history":
        parser.add_argument("chat_id")
        parser.add_argument("--start")
        parser.add_argument("--end")
        args = _parse(parser, arguments)
        return _response(wps.list_chat_messages(args.chat_id, start_time=args.start, end_time=args.end, with_sender_details=True))
    if shortcut == "+send":
        parser.add_argument("chat_id")
        parser.add_argument("text")
        parser.add_argument("--plain", action="store_true")
        args = _parse(parser, arguments)
        return _response(wps.send_message(args.chat_id, text=args.text, text_type=None if args.plain else "markdown"))
    if shortcut == "+recall":
        parser.add_argument("chat_id")
        parser.add_argument("message_id")
        args = _parse(parser, arguments)
        return _response(wps.recall_message(args.chat_id, args.message_id))
    raise validation(f"未知 im 快捷命令: {shortcut}")


HANDLERS: dict[str, Callable] = {
    "contact": contact,
    "calendar": calendar,
    "meeting": meeting,
    "drive": drive,
    "base": base,
    "im": im,
}
