# -*- coding: utf-8 -*-
"""
凭证文件存储。路径 ~/.config/wps365/credentials.json，权限 0o600。
"""
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

CRED_DIR = Path.home() / ".config" / "wps365"
CRED_FILE = CRED_DIR / "credentials.json"


def _ensure_dir() -> None:
    CRED_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(str(CRED_DIR), 0o700)


def load_credentials() -> dict | None:
    if not CRED_FILE.exists():
        return None
    try:
        with open(CRED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_credentials(data: dict) -> None:
    _ensure_dir()
    data["last_used_at"] = datetime.now(timezone.utc).isoformat()
    tmp = CRED_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.chmod(str(tmp), 0o600)
    tmp.replace(CRED_FILE)


def clear_credentials() -> None:
    if CRED_FILE.exists():
        CRED_FILE.unlink()


def update_last_used() -> None:
    cred = load_credentials()
    if cred:
        cred["last_used_at"] = datetime.now(timezone.utc).isoformat()
        save_credentials(cred)
