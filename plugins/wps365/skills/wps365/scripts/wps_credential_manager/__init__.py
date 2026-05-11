# -*- coding: utf-8 -*-
"""WPS 365 凭证管理器 - 从 agentspace 扩展剥离的 OAuth 认证能力"""

from .manager import login, get_sid, refresh, status, logout, test_sid, auto_refresh_if_expired

__all__ = [
    "login",
    "get_sid",
    "refresh",
    "status",
    "logout",
    "test_sid",
    "auto_refresh_if_expired",
]
