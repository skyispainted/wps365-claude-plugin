# -*- coding: utf-8 -*-
"""CLI 入口：python -m wps_credential_manager"""

import argparse
import json
import sys

from .manager import login, get_sid, refresh, status, logout, test_sid


def cmd_login(args):
    result = login(app_id=args.app_id or "", flow=args.flow or "")
    print(f"\n登录成功！用户: {result.get('nickname')} ({result.get('user_id')})")
    print("凭证已加密存储。")


def cmd_status(args):
    s = status()
    if s.get("configured"):
        print(f"状态: 已配置")
        print(f"  app_id: {s.get('app_id')}")
        print(f"  用户: {s.get('nickname')} ({s.get('user_id')})")
        print(f"  创建时间: {s.get('created_at')}")
        print(f"  最后使用: {s.get('last_used_at')}")
        print(f"  凭证文件: {s.get('cred_file')}")
    else:
        print("状态: 未配置")
    if s.get("env_sid"):
        print("  (环境变量 WPS_SID/wps_sid 已设置)")


def cmd_refresh(args):
    result = refresh(app_id="", flow=args.flow or "")
    print(f"\n刷新成功！用户: {result.get('nickname')} ({result.get('user_id')})")


def cmd_logout(args):
    logout()
    print("凭证已清除。")


def cmd_test(args):
    result = test_sid()
    if result.get("valid"):
        print(f"sid 有效！用户: {result['user'].get('nickname')}")
    else:
        print(f"sid 无效: {result['error']}")
        sys.exit(1)


def cmd_get_sid(args):
    """输出原始 sid 到 stdout（用于管道传递）"""
    sid = get_sid()
    sys.stdout.write(sid)


def main():
    parser = argparse.ArgumentParser(
        description="WPS 365 凭证管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("login", help="OAuth 登录获取 wps_sid")
    p.add_argument("--flow", choices=["cloud", "local"], default="",
                   help="OAuth 模式：cloud（生成链接）/ local（localhost 回调），默认自动检测")
    p.add_argument("--app-id", default="", help="指定 app_id（不指定则登录时输入）")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("status", help="查看凭证状态")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("refresh", help="手动刷新 wps_sid")
    p.add_argument("--flow", choices=["cloud", "local"], default="", help="OAuth 模式")
    p.set_defaults(func=cmd_refresh)

    p = sub.add_parser("logout", help="清除凭证")
    p.set_defaults(func=cmd_logout)

    p = sub.add_parser("test", help="测试当前 sid 是否有效")
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("get-sid", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_get_sid)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
