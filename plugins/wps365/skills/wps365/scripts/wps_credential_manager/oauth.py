# -*- coding: utf-8 -*-
"""
WPS Agentspace OAuth 登录流程（本地回调 + 云端轮询）。
精确对齐 agentspace/dist/src/auth.js 的行为。
"""
import json
import socket
import sys
import threading
import time
import urllib.request
import uuid
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import urlparse, parse_qs

LOGIN_CALLBACK_URL = "https://agentspace.wps.cn/v7/devhub/users/login_callback"
LOGIN_URL_ENDPOINT = "https://agentspace.wps.cn/v7/devhub/users/login_url"
USER_TOKEN_URL = "https://agentspace.wps.cn/v7/devhub/users/user_token"
GET_USER_URL = "https://agentspace.wps.cn/v7/devhub/users/current"
PORT = 11791
REDIRECT_URI = f"http://localhost:{PORT}/oauth-callback"
CLOUD_OAUTH_POLL_INTERVAL = 5
CLOUD_OAUTH_POLL_TIMEOUT = 5 * 60

from .html import LOGIN_SUCCESS_HTML


def _is_remote_env() -> bool:
    """检测是否在远程环境（WSL2、SSH、Docker 等）"""
    import os
    try:
        with open("/proc/version") as f:
            if "microsoft" in f.read().lower():
                return True  # WSL2
    except FileNotFoundError:
        pass
    if os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"):
        return True
    if os.environ.get("CONTAINER") or os.path.exists("/.dockerenv"):
        return True
    return False


def _get_user_info(token: str) -> dict:
    """获取当前用户信息"""
    req = urllib.request.Request(
        GET_USER_URL,
        headers={
            "Accept": "application/json",
            "Cookie": f"wps_sid={token}",
            "Referer": "https://agentspace.wps.cn/agents",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def login_cloud_oauth(app_id: str = "") -> dict:
    """
    云端服务端 OAuth：
    1. POST login_url 获取 code 和登录 URL
    2. 用户浏览器打开 URL 登录 WPS
    3. 轮询 user_token 直到拿到 token
    """
    state = str(uuid.uuid4())
    body = {"state": state}
    if app_id:
        body["app_id"] = app_id

    # Step 1: 获取登录地址
    req = urllib.request.Request(
        LOGIN_URL_ENDPOINT,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    code = (data.get("data", {}).get("code") or "").strip()
    auth_url = (data.get("data", {}).get("url") or "").strip()
    resp_app_id = (data.get("data", {}).get("app_id") or "").strip()

    if not code or not auth_url:
        raise ValueError(f"获取登录地址失败: {json.dumps(data)}")

    print("请在浏览器中打开下方链接，使用 WPS 账号登录。")
    print("登录完成后，本客户端将自动轮询获取凭证（每 5 秒一次，最多等待 5 分钟）。")
    print(f"\n请用本地浏览器打开: {auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    # Step 2: 轮询 user_token
    final_app_id = resp_app_id or app_id or ""
    deadline = time.time() + CLOUD_OAUTH_POLL_TIMEOUT
    poll_count = 0

    while time.time() < deadline:
        poll_count += 1
        remaining = int(deadline - time.time())
        print(f"  第 {poll_count} 次轮询，剩余 {remaining}s ...", end="\r")
        sys.stdout.flush()

        try:
            req = urllib.request.Request(
                USER_TOKEN_URL,
                data=json.dumps({"app_id": final_app_id, "code": code, "state": state}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read())
                token = (resp_data.get("data", {}).get("token") or "").strip()
                if token:
                    print()  # newline
                    user_info = _get_user_info(token)
                    return {
                        "token": token,
                        "nickname": user_info.get("data", {}).get("nickname"),
                        "user_id": user_info.get("data", {}).get("user_id"),
                    }
        except Exception:
            pass

        time.sleep(CLOUD_OAUTH_POLL_INTERVAL)

    print()
    raise TimeoutError("等待云端授权超时（5 分钟）")


def _parse_callback_input(input_str: str) -> dict:
    """解析用户粘贴的重定向 URL"""
    trimmed = input_str.strip()
    if not trimmed:
        return {"error": "未提供输入"}
    try:
        parsed = urlparse(trimmed)
        qs = parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        state = qs.get("state", [None])[0]
        if not code:
            return {"error": "URL 中缺少 code 参数"}
        if not state:
            return {"error": "URL 中缺少 state 参数"}
        app_id = qs.get("app_id", [None])[0]
        return {"code": code, "state": state, "appId": app_id}
    except Exception:
        return {"error": "请粘贴完整的重定向 URL（不仅是 code）"}


def login_local_oauth(app_id: str = "") -> dict:
    """
    本地 OAuth：
    1. 生成 state，构建 login_callback URL
    2. 浏览器打开，agentspace 验证 cookie 后重定向到 localhost
    3. 用 code + state + app_id 换取 token
    """
    state = str(uuid.uuid4())
    auth_url = f"{LOGIN_CALLBACK_URL}?cb={REDIRECT_URI}&state={state}"
    if app_id:
        auth_url += f"&app_id={app_id}"

    is_remote = _is_remote_env()
    callback_result: Optional[dict] = None
    callback_event = threading.Event()

    # 尝试启动本地回调服务器（非远程环境）
    if not is_remote:
        try:
            server = _start_callback_server(callback_result, callback_event)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
        except Exception:
            server = None
    else:
        server = None

    if not server:
        print("请在本地浏览器中打开下方 URL 完成授权。")
        print("（需要已登录 WPS 账号，浏览器会携带 cookie 自动完成授权）")
        print("授权完成后，请复制完整重定向 URL 粘贴回此处。")
        print(f"\n授权地址: {auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    code = ""
    callback_state = ""
    callback_app_id = ""

    if server:
        callback_event.wait(timeout=5 * 60)
        if callback_result is not None:
            code = callback_result.get("code", "")
            callback_state = callback_result.get("state", "")
            callback_app_id = callback_result.get("app_id", "")
        server.shutdown()
    else:
        raw = input("请粘贴重定向 URL: ")
        parsed = _parse_callback_input(raw)
        if "error" in parsed:
            raise ValueError(parsed["error"])
        code = parsed["code"]
        callback_state = parsed["state"]
        callback_app_id = parsed.get("appId") or ""

    if not code:
        raise ValueError("缺少 OAuth code")

    if callback_state != state:
        raise ValueError(f"state 不匹配：期望 {state}，收到 {callback_state}")

    final_app_id = callback_app_id or app_id or ""
    return _exchange_code_for_token(final_app_id, code, state)


def _start_callback_server(result_holder, event):
    """启动本地 HTTP 回调服务器"""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/oauth-callback":
                qs = parse_qs(parsed.query)
                result_holder["code"] = qs.get("code", [""])[0]
                result_holder["state"] = qs.get("state", [""])[0]
                result_holder["app_id"] = qs.get("app_id", [""])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(LOGIN_SUCCESS_HTML.encode())
                event.set()
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")

        def log_message(self, format, *args):
            pass  # suppress logs

    # Find available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", PORT))
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        sock.close()
        # Try alternative port
        for port in range(PORT + 1, PORT + 10):
            try:
                server = HTTPServer(("127.0.0.1", port), Handler)
                break
            except OSError:
                continue
        else:
            raise OSError("No available port for OAuth callback")
    finally:
        try:
            sock.close()
        except Exception:
            pass

    return server


def _exchange_code_for_token(app_id: str, code: str, state: str) -> dict:
    """用 code 换取 token"""
    req = urllib.request.Request(
        USER_TOKEN_URL,
        data=json.dumps({"app_id": app_id, "code": code, "state": state}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        token = (data.get("data", {}).get("token") or "").strip()
        if not token:
            raise ValueError("Token 交换未返回 access_token")

    user_info = _get_user_info(token)
    return {
        "token": token,
        "nickname": user_info.get("data", {}).get("nickname"),
        "user_id": user_info.get("data", {}).get("user_id"),
    }
