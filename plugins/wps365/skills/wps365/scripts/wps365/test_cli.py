# -*- coding: utf-8 -*-
"""Regression tests for the unified, agent-oriented WPS 365 CLI."""

import contextlib
import io
import json
import unittest
from unittest.mock import patch

from wps365.__main__ import main


class Wps365CliTest(unittest.TestCase):
    def invoke(self, arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(arguments)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def read_json(self, text):
        return json.loads(text)

    def test_schema_is_machine_readable_catalog(self):
        exit_code, stdout, stderr = self.invoke(["schema", "drive"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        payload = self.read_json(stdout)
        self.assertTrue(payload["ok"])
        self.assertIn("drive", payload["data"]["domains"])
        self.assertTrue(any(item["shortcut"] == "+read" for item in payload["data"]["commands"]))

    def test_schema_reports_unknown_domain_as_typed_error(self):
        exit_code, stdout, stderr = self.invoke(["schema", "unknown"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        payload = self.read_json(stderr)
        self.assertEqual(payload["error"]["type"], "validation")
        self.assertEqual(payload["error"]["subtype"], "invalid_argument")

    def test_high_risk_operation_requires_confirmation(self):
        exit_code, stdout, stderr = self.invoke(
            ["drive", "+move", "--drive", "private", "--file-id", "file-1", "--dst-parent-id", "root"]
        )

        self.assertEqual(exit_code, 10)
        self.assertEqual(stdout, "")
        payload = self.read_json(stderr)
        self.assertEqual(payload["error"]["type"], "confirmation")
        self.assertEqual(payload["error"]["subtype"], "confirmation_required")

    def test_dry_run_skips_client_call(self):
        with patch("wps365.handlers.wps.move_file") as move_file:
            exit_code, stdout, stderr = self.invoke(
                ["drive", "+move", "--dry-run", "--drive", "private", "--file-id", "file-1", "--dst-parent-id", "root"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        move_file.assert_not_called()
        payload = self.read_json(stdout)
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["data"]["command"], {"domain": "drive", "shortcut": "+move"})

    def test_dry_run_requires_flag_values(self):
        exit_code, stdout, stderr = self.invoke(["drive", "+move", "--dry-run", "--file-id", "file-1", "--dst-parent-id"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("--dst-parent-id", self.read_json(stderr)["error"]["message"])

    def test_direct_read_handler_uses_client_and_envelopes_data(self):
        with patch("wps365.handlers.wps.search_users", return_value={"code": 0, "data": {"items": [{"id": "u1"}]}}) as search_users:
            exit_code, stdout, stderr = self.invoke(["contact", "+search", "张三"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        search_users.assert_called_once_with("张三")
        self.assertEqual(self.read_json(stdout), {"ok": True, "data": {"items": [{"id": "u1"}]}})

    def test_api_failure_becomes_typed_stderr_error(self):
        with patch("wps365.handlers.wps.search_users", return_value={"code": 401, "msg": "Unauthorized"}):
            exit_code, stdout, stderr = self.invoke(["contact", "+search", "张三"])

        self.assertEqual(exit_code, 3)
        self.assertEqual(stdout, "")
        payload = self.read_json(stderr)
        self.assertEqual(payload["error"]["type"], "authentication")
        self.assertEqual(payload["error"]["subtype"], "credentials_invalid")

    def test_auth_status_is_structured_and_redacts_credentials(self):
        raw_status = {"configured": True, "app_id": "AK123", "nickname": "测试用户", "user_id": "u1", "cred_file": "secret-path"}
        with patch("wps365.handlers.manager.status", return_value=raw_status):
            exit_code, stdout, stderr = self.invoke(["auth", "status"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        payload = self.read_json(stdout)
        self.assertTrue(payload["data"]["configured"])
        self.assertTrue(payload["data"]["app_id_configured"])
        self.assertNotIn("app_id", payload["data"])
        self.assertNotIn("cred_file", payload["data"])


if __name__ == "__main__":
    unittest.main()
