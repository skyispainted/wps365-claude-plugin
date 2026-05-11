# -*- coding: utf-8 -*-
"""
凭证管理器：协调 OAuth 登录、加密存储、sid 获取与自动刷新。
"""
import sys
import time
from datetime import datetime, timezone

from .crypto import encrypt_wps_sid, decrypt_wps_sid
from .oauth import login_cloud_oauth, login_local_oauth, _get_user_info
from .store import load_credentials, save_credentials, clear_credentials


def login(app_id: str = "", flow: str = "") -> dict:
    """
    完整登录流程。
    flow: "cloud" | "local" | "" (auto-detect)
    """
    from .oauth import _is_remote_env

    if not flow:
        flow = "cloud" if _is_remote_env() else "local"

    if flow == "cloud":
        result = login_cloud_oauth(app_id)
    else:
        result = login_local_oauth(app_id)

    final_app_id = app_id or ""
    if not final_app_id:
        try:
            final_app_id = input("请输入 app_id（用于加密存储）: ").strip()
        except EOFError:
            raise ValueError("app_id 不能为空")

    encrypted = encrypt_wps_sid(result["token"], final_app_id)
    save_credentials({
        "app_id": final_app_id,
        "encrypted_token": encrypted,
        "nickname": result.get("nickname"),
        "user_id": result.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": datetime.now(timezone.utc).isoformat(),
    })
    return result


def get_sid() -> str:
    """
    获取 wps_sid。优先级：
    1. 环境变量 WPS_SID / wps_sid
    2. 加密凭证文件
    """
    import os
    sid = os.environ.get("WPS_SID") or os.environ.get("wps_sid")
    if sid:
        return sid

    cred = load_credentials()
    if not cred:
        raise ValueError("未找到凭证，请先运行: python -m wps_credential_manager login")

    try:
        sid = decrypt_wps_sid(cred["encrypted_token"], cred.get("app_id", ""))
    except Exception:
        raise ValueError("凭证解密失败，可能需要重新登录")

    return sid


def refresh(app_id: str = "", flow: str = "") -> dict:
    """重新运行 OAuth 获取新 token"""
    cred = load_credentials()
    if cred and not app_id:
        app_id = cred.get("app_id", "")
    return login(app_id=app_id, flow=flow)


def status() -> dict:
    """返回当前凭证状态"""
    import os
    from .store import CRED_FILE

    cred = load_credentials()
    result = {
        "configured": False,
        "env_sid": bool(os.environ.get("WPS_SID") or os.environ.get("wps_sid")),
    }

    if cred:
        result.update({
            "configured": True,
            "app_id": cred.get("app_id"),
            "nickname": cred.get("nickname"),
            "user_id": cred.get("user_id"),
            "created_at": cred.get("created_at"),
            "last_used_at": cred.get("last_used_at"),
            "cred_file": str(CRED_FILE),
        })
    return result


def logout() -> None:
    """清除凭证"""
    clear_credentials()


def test_sid() -> dict:
    """测试当前 sid 是否有效"""
    sid = get_sid()
    try:
        user_info = _get_user_info(sid)
        return {"valid": True, "user": user_info.get("data", {})}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def auto_refresh_if_expired() -> bool:
    """
    检测 sid 是否过期，如果是则自动刷新。
    返回 True 表示进行了刷新。
    """
    sid = get_sid()
    try:
        _get_user_info(sid)
        return False  # sid 有效，无需刷新
    except Exception:
        # sid 过期，尝试自动刷新
        cred = load_credentials()
        app_id = cred.get("app_id", "") if cred else ""
        if not app_id:
            return False
        # 优先尝试云端 OAuth（服务端 session 可能仍有效）
        try:
            login(app_id=app_id, flow="cloud")
            return True
        except Exception:
            # 云端 OAuth 失败，尝试本地
            try:
                login(app_id=app_id, flow="local")
                return True
            except Exception:
                return False
