# -*- coding: utf-8 -*-
"""Explicit compatibility route for low-frequency legacy script commands."""

from __future__ import annotations

import contextlib
import io
import runpy
import sys
from pathlib import Path
from typing import Sequence

from .errors import WpsCliError, validation


SCRIPTS_DIR = Path(__file__).resolve().parent.parent
LEGACY_DOMAINS = {"calendar", "contacts", "dbsheet", "drive", "im", "meeting", "user-current"}
BLOCKED_LEGACY_COMMANDS = {
    ("im", "recall"): "legacy im recall 不具备统一 CLI 的确认保护；请使用 `wps365 im +recall <chat_id> <message_id> --yes`。",
}


def run(arguments: Sequence[str]) -> dict:
    if len(arguments) < 2:
        raise validation("用法: wps365 legacy <domain> <legacy-command> [arguments]")
    domain, command, *forwarded = arguments
    if domain not in LEGACY_DOMAINS:
        raise validation(f"未知 legacy 域: {domain}")
    if message := BLOCKED_LEGACY_COMMANDS.get((domain, command)):
        raise validation(message)
    script = SCRIPTS_DIR / domain / "run.py"
    if not script.is_file():
        raise WpsCliError(f"未找到 legacy 脚本: {domain}", "internal", "legacy_missing")
    old_argv = sys.argv
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        sys.argv = [str(script), command, *forwarded]
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                runpy.run_path(str(script), run_name="__main__")
        except SystemExit as error:
            if error.code not in (None, 0):
                message = stderr.getvalue().strip() or "legacy 命令失败"
                raise WpsCliError(message, "api", "legacy_command_failed") from error
    finally:
        sys.argv = old_argv
    return {
        "legacy": True,
        "domain": domain,
        "command": command,
        "output": stdout.getvalue().strip(),
        "warnings": stderr.getvalue().strip() or None,
    }
