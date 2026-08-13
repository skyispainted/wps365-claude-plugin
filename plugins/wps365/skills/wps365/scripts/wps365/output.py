# -*- coding: utf-8 -*-
"""Wire-format emitters for the unified WPS CLI."""

from __future__ import annotations

import json
import sys
from typing import Any


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))


def success(data: Any = None, *, meta: dict | None = None, dry_run: bool = False) -> None:
    payload: dict[str, Any] = {"ok": True, "data": data if data is not None else {}}
    if meta:
        payload["meta"] = meta
    if dry_run:
        payload["dry_run"] = True
    print(_json(payload))


def failure(error) -> None:
    print(_json(error.payload()), file=sys.stderr)


def pretty(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
