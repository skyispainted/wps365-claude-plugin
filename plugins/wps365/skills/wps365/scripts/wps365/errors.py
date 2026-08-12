# -*- coding: utf-8 -*-
"""Typed, machine-readable failures for the unified WPS CLI."""

from __future__ import annotations

from dataclasses import dataclass


EXIT_CODES = {
    "validation": 2,
    "authentication": 3,
    "authorization": 4,
    "network": 6,
    "confirmation": 10,
    "api": 1,
    "internal": 1,
}


@dataclass
class WpsCliError(Exception):
    message: str
    category: str = "internal"
    subtype: str = "unexpected"
    hint: str | None = None
    code: int | str | None = None
    retryable: bool = False

    @property
    def exit_code(self) -> int:
        return EXIT_CODES.get(self.category, 1)

    def payload(self) -> dict:
        error = {
            "type": self.category,
            "subtype": self.subtype,
            "message": self.message,
        }
        if self.hint:
            error["hint"] = self.hint
        if self.code is not None:
            error["code"] = self.code
        if self.retryable:
            error["retryable"] = True
        return {"ok": False, "error": error}


def validation(message: str, hint: str | None = None) -> WpsCliError:
    return WpsCliError(message, "validation", "invalid_argument", hint)


def confirmation(action: str) -> WpsCliError:
    return WpsCliError(
        f"操作需要明确确认: {action}",
        "confirmation",
        "confirmation_required",
        "核对目标和参数后，获得用户明确同意时追加 --yes 重试。",
    )


def from_response(response: dict) -> WpsCliError | None:
    if not isinstance(response, dict) or response.get("code") in (None, 0):
        return None
    code = response.get("code")
    message = response.get("msg") or response.get("message") or "WPS API 请求失败"
    lowered = str(message).lower()
    if code in (401, 400401) or any(token in lowered for token in ("unauthorized", "not_login", "csrf", "sid")):
        return WpsCliError(
            message,
            "authentication",
            "credentials_invalid",
            "运行 `python -m wps365 auth status --verify` 检查凭证；失效时重新执行登录。",
            code,
        )
    if code in (403, 400403) or any(token in lowered for token in ("permission", "forbidden", "denied")):
        return WpsCliError(message, "authorization", "permission_denied", None, code)
    if any(token in lowered for token in ("timeout", "temporarily", "rate limit", "frequency")):
        return WpsCliError(message, "network", "temporary_failure", "稍后重试；不要重复执行非幂等写操作。", code, True)
    return WpsCliError(message, "api", "request_failed", None, code)
