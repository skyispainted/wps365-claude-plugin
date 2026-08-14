# -*- coding: utf-8 -*-
"""Direct, agent-oriented handlers built on the existing WPS client package."""

from __future__ import annotations

import argparse
import json
import tempfile
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
    if not isinstance(response, dict) or response.get("code") is None:
        raise WpsCliError(
            "WPS API 返回了空或无效响应",
            "network",
            "invalid_response",
            "稍后重试；不要重复执行非幂等写操作。",
            retryable=True,
        )
    if response.get("code") == -1 and response.get("msg") == "response is not json":
        raise WpsCliError(
            "WPS API 返回了非 JSON 响应",
            "network",
            "invalid_response",
            "稍后重试；不要重复执行非幂等写操作。",
            retryable=True,
        )
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


def _resolve_direct_file(file_id: str, drive: str | None) -> tuple[dict, str]:
    data = _response(wps.get_file_directly(file_id, with_drive=True))
    drive_data = data.get("drive")
    drive_id = data.get("drive_id") or (
        drive_data.get("id") if isinstance(drive_data, dict) else None
    )
    return data, str(drive_id or _drive_id(drive))


def _drive_search_result(item: object) -> object:
    if not isinstance(item, dict):
        return item
    result = dict(item)
    file_src = result.get("file_src")
    is_link_source = isinstance(file_src, dict) and file_src.get("type") == "link"
    link_id = result.get("link_id")
    file_id = result.get("id")
    if is_link_source and link_id:
        result["read_args"] = ["--link-id", str(link_id)]
    elif file_id:
        result["read_args"] = [str(file_id)]
    elif link_id:
        result["read_args"] = ["--link-id", str(link_id)]
    return result


def _drive_search_results(data: dict) -> dict:
    items = data.get("items")
    if not isinstance(items, list):
        return data
    return {**data, "items": [_drive_search_result(item) for item in items]}


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
    if shortcut == "+calendar-list":
        parser.add_argument("--page-size", type=int, default=20)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        return _response(wps.list_calendars(page_size=args.page_size, page_token=args.page_token))
    if shortcut == "+calendar-get":
        parser.add_argument("calendar_id")
        args = _parse(parser, arguments)
        return _response(wps.get_calendar(args.calendar_id))
    if shortcut == "+calendar-create":
        parser.add_argument("--title", required=True)
        parser.add_argument("--color", required=True)
        parser.add_argument("--desc", default="")
        args = _parse(parser, arguments)
        return _response(wps.create_calendar(args.title, args.color, args.desc))
    if shortcut == "+calendar-update":
        parser.add_argument("calendar_id")
        parser.add_argument("--title")
        parser.add_argument("--color")
        parser.add_argument("--desc")
        args = _parse(parser, arguments)
        if not any((args.title, args.color, args.desc)):
            raise validation("请至少提供一个更新字段")
        return _response(wps.update_calendar(args.calendar_id, summary=args.title, color=args.color, description=args.desc))
    if shortcut == "+calendar-delete":
        parser.add_argument("calendar_id")
        args = _parse(parser, arguments)
        return _response(wps.delete_calendar(args.calendar_id))
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
    if shortcut in ("+participants", "+participant-list", "+participant-add", "+participant-remove"):
        parser.add_argument("--meeting-id", required=True)
        parser.add_argument("--action", choices=("list", "add", "remove"))
        parser.add_argument("--ids")
        args = _parse(parser, arguments)
        action_by_shortcut = {
            "+participant-list": "list",
            "+participant-add": "add",
            "+participant-remove": "remove",
        }
        action = action_by_shortcut.get(shortcut, args.action or "list")
        if action == "list":
            return _response(wps.list_meeting_participants(args.meeting_id))
        ids = _csv(args.ids)
        if not ids:
            raise validation("添加或移除参会人时请提供 --ids")
        function = wps.put_meeting_participants if action == "add" else wps.delete_meeting_participants
        return _response(function(args.meeting_id, ids))
    if shortcut == "+room-level-list":
        parser.add_argument("--room-level-id")
        parser.add_argument("--direct-access", action="store_true")
        parser.add_argument("--page-size", type=int, default=20)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        return _response(wps.list_meeting_room_levels(args.room_level_id, args.direct_access, args.page_size, args.page_token))
    if shortcut == "+event-room-list":
        parser.add_argument("--calendar-id", default="primary")
        parser.add_argument("--event-id", required=True)
        args = _parse(parser, arguments)
        return _response(wps.list_event_meeting_rooms(args.calendar_id, args.event_id))
    if shortcut == "+started-list":
        parser.add_argument("--start", required=True)
        parser.add_argument("--end", required=True)
        parser.add_argument("--join-code")
        parser.add_argument("--page-size", type=int, default=20)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        return _response(wps.list_started_meetings(args.start, args.end, args.join_code, args.page_token, args.page_size))
    if shortcut in ("+recording-list", "+minute-list"):
        parser.add_argument("--meeting-id", required=True)
        args = _parse(parser, arguments)
        function = wps.meeting_get_recordings if shortcut == "+recording-list" else wps.meeting_get_minutes
        return _response(function(args.meeting_id))
    if shortcut in ("+recording-summary", "+recording-transcript"):
        parser.add_argument("--meeting-id", required=True)
        parser.add_argument("--recording-id", required=True)
        args = _parse(parser, arguments)
        function = wps.get_recording_summary if shortcut == "+recording-summary" else wps.get_recording_transcript
        return _response(function(args.meeting_id, args.recording_id))
    if shortcut in ("+minute-summary", "+minute-transcript"):
        parser.add_argument("--meeting-id", required=True)
        parser.add_argument("--minute-id", required=True)
        args = _parse(parser, arguments)
        function = wps.get_minute_summary if shortcut == "+minute-summary" else wps.get_minute_transcript
        return _response(function(args.meeting_id, args.minute_id))
    if shortcut == "+artifact-export":
        parser.add_argument("--meeting-id", required=True)
        parser.add_argument("--kind", choices=("recordings", "minutes"), required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--include", choices=("summary", "transcript", "both"), default="both")
        args = _parse(parser, arguments)
        output_dir = Path(args.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        list_function = wps.meeting_get_recordings if args.kind == "recordings" else wps.meeting_get_minutes
        artifact_id = "recording_id" if args.kind == "recordings" else "minute_id"
        artifacts = _response(list_function(args.meeting_id)).get("items") or []
        exported: list[str] = []
        for index, artifact in enumerate(artifacts, start=1):
            identifier = str(artifact.get("id") or artifact.get(artifact_id) or "")
            if not identifier:
                continue
            payload = {"meeting_id": args.meeting_id, "kind": args.kind, "artifact": artifact}
            if args.include in ("summary", "both"):
                function = wps.get_recording_summary if args.kind == "recordings" else wps.get_minute_summary
                payload["summary"] = _response(function(args.meeting_id, identifier))
            if args.include in ("transcript", "both"):
                function = wps.get_recording_transcript if args.kind == "recordings" else wps.get_minute_transcript
                payload["transcript"] = _response(function(args.meeting_id, identifier))
            target = output_dir / f"{args.kind}-{index:03d}-{identifier}.json"
            if target.exists():
                raise validation(f"导出文件已存在: {target}")
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            exported.append(str(target))
        return {"meeting_id": args.meeting_id, "kind": args.kind, "count": len(exported), "files": exported}
    raise validation(f"未知 meeting 快捷命令: {shortcut}")


def drive(shortcut: str, arguments: Sequence[str]) -> dict:
    parser = _parser(f"drive {shortcut}")
    if shortcut == "+recent":
        parser.add_argument("--page-size", type=int, default=50)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        return _response(wps.list_latest_items(page_size=args.page_size, page_token=args.page_token))
    if shortcut == "+favorite-list":
        parser.add_argument("--page-size", type=int, default=50)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        return _response(wps.list_star_items(page_size=args.page_size, page_token=args.page_token))
    if shortcut in ("+favorite-add", "+favorite-remove"):
        parser.add_argument("file_ids", nargs="+")
        args = _parse(parser, arguments)
        function = wps.batch_create_star_items if shortcut == "+favorite-add" else wps.batch_delete_star_items
        return _response(function(args.file_ids))
    if shortcut == "+trash-list":
        parser.add_argument("--drive")
        parser.add_argument("--page-size", type=int, default=20)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        drive_id = _drive_id(args.drive) if args.drive else None
        return _response(wps.list_deleted_files(drive_id, page_size=args.page_size, page_token=args.page_token))
    if shortcut == "+download-url":
        parser.add_argument("--file-id", required=True)
        parser.add_argument("--drive", default="private")
        args = _parse(parser, arguments)
        return _response(wps.get_file_download_url(_drive_id(args.drive), args.file_id))
    if shortcut == "+name-check":
        parser.add_argument("name")
        parser.add_argument("--parent", default="root")
        parser.add_argument("--drive", default="private")
        args = _parse(parser, arguments)
        return _response(wps.check_name_exists(_drive_id(args.drive), args.parent, args.name))
    if shortcut == "+label-list":
        parser.add_argument("--page-size", type=int, default=20)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        return _response(wps.list_drive_labels(page_size=args.page_size, page_token=args.page_token))
    if shortcut == "+label-get":
        parser.add_argument("label_id")
        args = _parse(parser, arguments)
        return _response(wps.get_drive_label_meta(args.label_id))
    if shortcut == "+label-create":
        parser.add_argument("name")
        args = _parse(parser, arguments)
        return _response(wps.create_drive_label(args.name))
    if shortcut == "+label-object-list":
        parser.add_argument("label_id")
        parser.add_argument("--page-size", type=int, default=20)
        parser.add_argument("--page-token")
        args = _parse(parser, arguments)
        return _response(wps.list_drive_label_objects(args.label_id, page_size=args.page_size, page_token=args.page_token))
    if shortcut in ("+label-add", "+label-remove"):
        parser.add_argument("label_id")
        parser.add_argument("file_ids", nargs="+")
        args = _parse(parser, arguments)
        function = wps.batch_add_drive_label_objects if shortcut == "+label-add" else wps.batch_remove_drive_label_objects
        return _response(function(args.label_id, args.file_ids))
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
        return _drive_search_results(_response(wps.search_files(args.keyword, search_type=args.type)))
    if shortcut in ("+get", "+read"):
        parser.add_argument("file_id", nargs="?")
        parser.add_argument("--link-id")
        parser.add_argument("--drive", default="private")
        parser.add_argument("--format", choices=("plain", "markdown", "html", "kdc"))
        args = _parse(parser, arguments)
        if bool(args.file_id) == bool(args.link_id):
            raise validation("请提供 file_id，或使用 --link-id 提供分享链接 ID（二者只能选一个）")
        if args.file_id:
            metadata, drive_id = _resolve_direct_file(args.file_id, args.drive)
            if shortcut == "+get":
                return metadata
            file_id = args.file_id
        else:
            file_id, drive_id = _resolve_link(args.link_id, args.drive)
            if shortcut == "+get":
                return _response(wps.get_file(drive_id, file_id))
        requested_format = args.format or "markdown"
        try:
            return _response(wps.get_file_content_extract(drive_id, file_id, format=requested_format))
        except WpsCliError as error:
            if args.format is None and error.category == "api":
                return _response(wps.get_file_content_extract(drive_id, file_id, format="plain"))
            raise
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
            raise validation("统一写入当前仅支持智能文档 (.otl)", "其它格式请使用 `drive +overwrite` 或 `drive +convert-overwrite`，并先完成 dry-run/确认流程。")
        wps.write_airpage_content(args.file_id, args.title or data.get("name") or "文档", args.content, pos="begin")
        return {"file_id": args.file_id, "written": True}
    if shortcut in ("+overwrite", "+convert-overwrite"):
        parser.add_argument("--file-id", required=True)
        parser.add_argument("--drive", default="private")
        parser.add_argument("--source")
        parser.add_argument("--content")
        parser.add_argument("--format", choices=("docx", "pdf"))
        parser.add_argument("--template")
        args = _parse(parser, arguments)
        if shortcut == "+overwrite" and (not args.source or args.content or args.format):
            raise validation("覆盖文档需要且仅接受 --source")
        if shortcut == "+convert-overwrite" and bool(args.source) == bool(args.content):
            raise validation("转换覆盖需要 --source 或 --content（二者只能选一个）")
        if shortcut == "+convert-overwrite" and not args.format:
            raise validation("转换覆盖需要 --format docx 或 --format pdf")
        source = Path(args.source).expanduser() if args.source else None
        if source and not source.is_file():
            raise validation(f"文件不存在: {source}")
        metadata = _response(wps.get_file_directly(args.file_id))
        if str(metadata.get("name") or "").lower().endswith(".otl"):
            raise validation(".otl 智能文档请使用 `drive file write`，不能使用版本覆盖")
        drive_id = _drive_id(args.drive)
        temporary_paths: list[Path] = []
        try:
            if shortcut == "+convert-overwrite":
                if args.content is not None:
                    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
                    handle.write(args.content)
                    handle.close()
                    source = Path(handle.name)
                    temporary_paths.append(source)
                converted = wps.convert_file(str(source), args.format, args.template if args.format == "docx" else None)
                content = _response(converted)
                if not isinstance(content, bytes):
                    raise validation("文件转换未返回二进制内容")
                handle = tempfile.NamedTemporaryFile(mode="wb", suffix=f".{args.format}", delete=False)
                handle.write(content)
                handle.close()
                source = Path(handle.name)
                temporary_paths.append(source)
            return _response(wps.update_file(args.file_id, str(source), drive_id))
        finally:
            for temporary_path in temporary_paths:
                temporary_path.unlink(missing_ok=True)
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
        parser.add_argument("--role-id")
        parser.add_argument("--opts")
        parser.add_argument("--mode", default="pause")
        args = _parse(parser, arguments)
        drive_id = _drive_id(args.drive)
        if shortcut == "+share":
            opts = _json(args.opts, "--opts") if args.opts else None
            if opts is not None and not isinstance(opts, dict):
                raise validation("--opts 必须是 JSON 对象")
            return _response(wps.open_file_link(drive_id, args.file_id, opts=opts, role_id=args.role_id, scope=args.scope))
        return _response(wps.close_file_link(drive_id, args.file_id, mode=args.mode))
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
    if shortcut == "+sheet-create":
        parser.add_argument("--name")
        parser.add_argument("--fields")
        parser.add_argument("--views")
        args = _parse(parser, arguments)
        fields = _json(args.fields, "--fields") if args.fields else None
        views = _json(args.views, "--views") if args.views else None
        if fields is not None and not isinstance(fields, list):
            raise validation("--fields 必须是字段数组")
        if views is not None and not isinstance(views, list):
            raise validation("--views 必须是视图数组")
        return _response(wps.dbsheet_create_sheet(args.file_id, name=args.name, fields=fields, views=views))
    parser.add_argument("sheet_id", type=int)
    if shortcut == "+sheet-update":
        parser.add_argument("--name", required=True)
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_update_sheet(args.file_id, args.sheet_id, name=args.name))
    if shortcut == "+sheet-delete":
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_delete_sheet(args.file_id, args.sheet_id))
    if shortcut == "+view-create":
        parser.add_argument("--name")
        parser.add_argument("--type", choices=("Grid", "Kanban", "Gallery", "Form", "Gantt", "Query"))
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_create_view(args.file_id, args.sheet_id, name=args.name, view_type=args.type))
    if shortcut == "+form-get":
        parser.add_argument("view_id")
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_get_form_meta(args.file_id, args.sheet_id, args.view_id))
    if shortcut == "+form-update":
        parser.add_argument("view_id")
        parser.add_argument("--name")
        parser.add_argument("--desc")
        args = _parse(parser, arguments)
        if not any((args.name, args.desc)):
            raise validation("请至少提供 --name 或 --desc")
        return _response(wps.dbsheet_update_form_meta(args.file_id, args.sheet_id, args.view_id, name=args.name, description=args.desc))
    if shortcut == "+list":
        parser.add_argument("--page-size", type=int, default=20)
        parser.add_argument("--page-token")
        parser.add_argument("--filter")
        args = _parse(parser, arguments)
        return _response(wps.dbsheet_list_records(args.file_id, args.sheet_id, page_size=args.page_size, page_token=args.page_token, filter_body=_json(args.filter, "--filter") if args.filter else None))
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
    if shortcut == "+recent":
        parser.add_argument("--page-size", type=int, default=50)
        parser.add_argument("--page-token")
        parser.add_argument("--start")
        parser.add_argument("--end")
        parser.add_argument("--unread", action="store_true")
        parser.add_argument("--mention-me", action="store_true")
        args = _parse(parser, arguments)
        return _response(wps.list_recent_chats(page_size=args.page_size, page_token=args.page_token, start_time=args.start, end_time=args.end, filter_unread=args.unread, filter_mention_me=args.mention_me))
    if shortcut == "+message-search":
        parser.add_argument("keyword", nargs="?")
        parser.add_argument("--chat-ids")
        parser.add_argument("--sender-ids")
        parser.add_argument("--start")
        parser.add_argument("--end")
        parser.add_argument("--page-size", type=int, default=20)
        args = _parse(parser, arguments)
        if not any((args.keyword, args.chat_ids, args.sender_ids, args.start, args.end)):
            raise validation("全局搜索消息至少需要关键词、会话、发送者或时间范围")
        return _response(wps.search_messages(args.keyword, page_size=args.page_size, chat_id_list=_csv(args.chat_ids), sender_id_list=_csv(args.sender_ids), start_time=args.start, end_time=args.end, with_sender_details=True))
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
    if shortcut in ("+send-rich", "+send-image", "+send-file", "+send-card"):
        parser.add_argument("chat_id")
        parser.add_argument("--json", required=True)
        parser.add_argument("--quote-message-id")
        args = _parse(parser, arguments)
        payload = _json(args.json, "--json")
        if not isinstance(payload, dict):
            raise validation("--json 必须是 JSON 对象")
        payload_by_shortcut = {
            "+send-rich": ("rich_text", "rich_text"),
            "+send-image": ("image", "image"),
            "+send-file": ("file", "file"),
            "+send-card": ("card", "card"),
        }
        message_type, field = payload_by_shortcut[shortcut]
        if shortcut == "+send-file" and payload.get("type") not in ("local", "cloud"):
            raise validation("文件消息必须包含 type: local 或 cloud")
        return _response(wps.send_message(args.chat_id, msg_type=message_type, quote_msg_id=args.quote_message_id, **{field: payload}))
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
