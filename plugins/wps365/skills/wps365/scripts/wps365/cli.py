# -*- coding: utf-8 -*-
"""Root dispatcher for the unified WPS 365 CLI."""

from __future__ import annotations

import sys
from typing import Sequence

from .catalog import BY_PATH, schema
from .errors import WpsCliError, confirmation, validation
from .handlers import HANDLERS, auth, config, whoami
from .legacy import run as legacy_run
from .output import failure, success


USAGE = """用法:
  python -m wps365 auth <status|login|refresh|logout|test> [flags]
  python -m wps365 config <status|doctor>
  python -m wps365 whoami
  python -m wps365 schema [domain] [+shortcut]
  python -m wps365 <domain> <+shortcut> [flags]
  python -m wps365 legacy <domain> <legacy-command> [arguments]

业务域: contact, calendar, meeting, drive, base, im
所有常用命令默认输出机器可读 JSON；高风险操作先 --dry-run，用户明确确认后才追加 --yes。
"""


def _emit_help() -> int:
    print(USAGE)
    return 0


def _flag_values(arguments: Sequence[str]) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for index, argument in enumerate(arguments):
        if argument.startswith("--"):
            values[argument] = arguments[index + 1] if index + 1 < len(arguments) and not arguments[index + 1].startswith("--") else None
    return values


def _positional_values(arguments: Sequence[str]) -> list[str]:
    values: list[str] = []
    index = 0
    while index < len(arguments):
        if arguments[index].startswith("--"):
            index += 2
        else:
            values.append(arguments[index])
            index += 1
    return values


def _validate_dry_run(domain: str, shortcut: str, arguments: Sequence[str]) -> None:
    flags = _flag_values(arguments)
    required_flags = {
        ("calendar", "+delete"): {"--event-id"},
        ("meeting", "+cancel"): {"--meeting-id"},
        ("drive", "+move"): {"--file-id", "--dst-parent-id"},
        ("drive", "+share"): {"--file-id"},
        ("drive", "+unshare"): {"--file-id"},
    }
    missing = sorted(flag for flag in required_flags.get((domain, shortcut), set()) if not flags.get(flag))
    if missing:
        raise validation(f"dry-run 缺少必填参数: {', '.join(missing)}")
    positionals = _positional_values(arguments)
    if (domain, shortcut) == ("base", "+delete") and len(positionals) < 3:
        raise validation("dry-run 需要 file_id、sheet_id 和至少一个 record_id")
    if (domain, shortcut) == ("im", "+recall") and len(positionals) < 2:
        raise validation("dry-run 需要 chat_id 和 message_id")


def _business(domain: str, shortcut: str, arguments: Sequence[str]) -> tuple[dict, bool]:
    spec = BY_PATH.get((domain, shortcut))
    if not spec:
        raise validation(f"未知快捷命令: {domain} {shortcut}", "运行 `python -m wps365 schema <domain>` 查看可用快捷命令。")
    forwarded = list(arguments)
    dry_run = "--dry-run" in forwarded
    confirmed = "--yes" in forwarded
    forwarded = [argument for argument in forwarded if argument not in {"--dry-run", "--yes"}]
    if dry_run:
        _validate_dry_run(domain, shortcut, forwarded)
        return {
            "command": {"domain": domain, "shortcut": shortcut},
            "risk": spec.risk,
            "inputs": forwarded,
        }, True
    if spec.risk == "high-risk-write" and not confirmed:
        raise confirmation(f"{domain} {shortcut}")
    try:
        return HANDLERS[domain](shortcut, forwarded), False
    except ValueError as error:
        raise validation(str(error)) from error


def main(arguments: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = list(arguments if arguments is not None else sys.argv[1:])
    try:
        if not args or args[0] in {"-h", "--help", "help"}:
            return _emit_help()
        root, *rest = args
        if root == "schema":
            if len(rest) > 2:
                raise validation("schema 最多接受 domain 和 +shortcut")
            success(schema(*(rest + [None] * (2 - len(rest)))))
            return 0
        if root == "auth":
            success(auth(rest))
            return 0
        if root == "config":
            success(config(rest))
            return 0
        if root == "whoami":
            success(whoami(rest))
            return 0
        if root == "legacy":
            success(legacy_run(rest))
            return 0
        if root not in HANDLERS:
            raise validation(f"未知命令域: {root}", "运行 `python -m wps365 schema` 查看可用命令域。")
        if not rest:
            raise validation(f"{root} 需要快捷命令", f"运行 `python -m wps365 schema {root}` 查看可用命令。")
        result, dry_run = _business(root, rest[0], rest[1:])
        success(result, dry_run=dry_run)
        return 0
    except WpsCliError as error:
        failure(error)
        return error.exit_code
    except ValueError as error:
        wrapped = validation(str(error))
        failure(wrapped)
        return wrapped.exit_code
    except Exception as error:
        wrapped = WpsCliError(str(error) or type(error).__name__, "internal", "unexpected")
        failure(wrapped)
        return wrapped.exit_code
