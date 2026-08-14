# -*- coding: utf-8 -*-
"""Regression tests for the unified, agent-oriented WPS 365 CLI."""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
        self.assertEqual(
            payload["data"]["command"],
            {"domain": "drive", "shortcut": "+move", "subcommand": ["file", "move"]},
        )

    def test_dry_run_requires_flag_values(self):
        exit_code, stdout, stderr = self.invoke(["drive", "+move", "--dry-run", "--file-id", "file-1", "--dst-parent-id"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("--dst-parent-id", self.read_json(stderr)["error"]["message"])

    def test_dry_run_requires_an_existing_drive_source_file(self):
        exit_code, stdout, stderr = self.invoke(
            ["drive", "+overwrite", "--dry-run", "--file-id", "file-1", "--source", "missing.docx"]
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("文件不存在", self.read_json(stderr)["error"]["message"])

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

    def test_drive_search_returns_canonical_read_args(self):
        response = {
            "code": 0,
            "data": {
                "items": [
                    {"id": "shared-file", "link_id": "link-1", "file_src": {"type": "link"}},
                    {"id": "own-file", "file_src": {"type": "private"}},
                ]
            },
        }
        with patch("wps365.handlers.wps.search_files", return_value=response) as search_files:
            exit_code, stdout, stderr = self.invoke(["drive", "+search", "项目方案"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        search_files.assert_called_once_with("项目方案", search_type="all")
        items = self.read_json(stdout)["data"]["items"]
        self.assertEqual(items[0]["read_args"], ["--link-id", "link-1"])
        self.assertEqual(items[1]["read_args"], ["own-file"])

    def test_drive_read_by_link_id_resolves_link_before_extracting(self):
        with patch("wps365.handlers.wps.get_link_meta", return_value={"code": 0, "data": {"file_id": "shared-file", "drive_id": "shared-drive"}}) as get_link_meta, patch("wps365.handlers.wps.get_file_content_extract", return_value={"code": 0, "data": {"markdown": "# 文档"}}) as extract:
            exit_code, stdout, stderr = self.invoke(["drive", "+read", "--link-id", "link-1"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        get_link_meta.assert_called_once_with("link-1")
        extract.assert_called_once_with("shared-drive", "shared-file", format="markdown")
        self.assertEqual(self.read_json(stdout)["data"], {"markdown": "# 文档"})

    def test_drive_read_by_file_id_uses_direct_metadata_without_drive_lookup(self):
        with patch("wps365.handlers.wps.get_file_directly", return_value={"code": 0, "data": {"drive_id": "own-drive"}}) as get_file_directly, patch("wps365.handlers.wps.get_drive_id") as get_drive_id, patch("wps365.handlers.wps.get_file_content_extract", return_value={"code": 0, "data": {"markdown": "# 文档"}}) as extract:
            exit_code, stdout, stderr = self.invoke(["drive", "+read", "own-file"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        get_file_directly.assert_called_once_with("own-file", with_drive=True)
        get_drive_id.assert_not_called()
        extract.assert_called_once_with("own-drive", "own-file", format="markdown")
        self.assertEqual(self.read_json(stdout)["data"], {"markdown": "# 文档"})

    def test_drive_read_retries_plain_only_when_default_format_fails(self):
        with patch("wps365.handlers.wps.get_file_directly", return_value={"code": 0, "data": {"drive_id": "own-drive"}}), patch("wps365.handlers.wps.get_file_content_extract", side_effect=[{"code": 400, "msg": "format markdown is unsupported"}, {"code": 0, "data": {"plain": "正文"}}]) as extract:
            exit_code, stdout, stderr = self.invoke(["drive", "+read", "own-file"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(extract.call_args_list[0].kwargs["format"], "markdown")
        self.assertEqual(extract.call_args_list[1].kwargs["format"], "plain")
        self.assertEqual(self.read_json(stdout)["data"], {"plain": "正文"})

    def test_drive_read_does_not_change_an_explicit_format(self):
        with patch("wps365.handlers.wps.get_file_directly", return_value={"code": 0, "data": {"drive_id": "own-drive"}}), patch("wps365.handlers.wps.get_file_content_extract", return_value={"code": 400, "msg": "format html is unsupported"}) as extract:
            exit_code, stdout, stderr = self.invoke(["drive", "+read", "own-file", "--format", "html"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        extract.assert_called_once_with("own-drive", "own-file", format="html")

    def test_schema_exposes_structured_subcommands(self):
        exit_code, stdout, stderr = self.invoke(["schema", "drive", "recent", "list"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        command = self.read_json(stdout)["data"]["commands"][0]
        self.assertEqual(command["shortcut"], "+recent")
        self.assertEqual(command["subcommand"], ["recent", "list"])
        self.assertEqual(command["invocation"], "drive recent list")

    def test_structured_read_path_invokes_existing_handler(self):
        with patch("wps365.handlers.wps.list_latest_items", return_value={"code": 0, "data": {"items": []}}) as list_latest:
            exit_code, stdout, stderr = self.invoke(["drive", "recent", "list", "--page-size", "10"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        list_latest.assert_called_once_with(page_size=10, page_token=None)
        self.assertEqual(self.read_json(stdout)["data"], {"items": []})

    def test_structured_high_risk_path_requires_confirmation(self):
        exit_code, stdout, stderr = self.invoke(["base", "sheet", "delete", "file-1", "1"])

        self.assertEqual(exit_code, 10)
        self.assertEqual(stdout, "")
        self.assertEqual(self.read_json(stderr)["error"]["type"], "confirmation")

    def test_message_search_requires_a_real_query(self):
        exit_code, stdout, stderr = self.invoke(["im", "message", "search"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(self.read_json(stderr)["error"]["type"], "validation")

    def test_document_overwrite_requires_confirmation(self):
        exit_code, stdout, stderr = self.invoke(["drive", "file", "overwrite", "--file-id", "file-1", "--source", "draft.docx"])

        self.assertEqual(exit_code, 10)
        self.assertEqual(stdout, "")
        self.assertEqual(self.read_json(stderr)["error"]["type"], "confirmation")

    def test_rich_message_requires_object_payload(self):
        exit_code, stdout, stderr = self.invoke(["im", "message", "send-card", "chat-1", "--json", "[]"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(self.read_json(stderr)["error"]["type"], "validation")

    def test_rich_message_routes_valid_payload(self):
        with patch("wps365.handlers.wps.send_message", return_value={"code": 0, "data": {"id": "m1"}}) as send_message:
            exit_code, stdout, stderr = self.invoke(["im", "message", "send-card", "chat-1", "--json", '{"i18n_items": []}'])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        send_message.assert_called_once_with("chat-1", msg_type="card", quote_msg_id=None, card={"i18n_items": []})
        self.assertEqual(self.read_json(stdout)["data"], {"id": "m1"})

    def test_meeting_export_writes_requested_directory(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with patch("wps365.handlers.wps.meeting_get_recordings", return_value={"code": 0, "data": {"items": [{"id": "r1"}]}}), patch("wps365.handlers.wps.get_recording_summary", return_value={"code": 0, "data": {"content": "summary"}}):
                exit_code, stdout, stderr = self.invoke(["meeting", "artifact", "export", "--meeting-id", "m1", "--kind", "recordings", "--include", "summary", "--output-dir", output_dir])

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr, "")
            payload = self.read_json(stdout)["data"]
            self.assertEqual(payload["count"], 1)
            exported = Path(payload["files"][0])
            self.assertTrue(exported.is_file())
            self.assertEqual(json.loads(exported.read_text(encoding="utf-8"))["summary"], {"content": "summary"})

    def test_bundled_launcher_ignores_user_site_cli(self):
        launcher = Path(__file__).resolve().parents[1] / "run_wps365.py"
        environment = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        result = subprocess.run(
            [sys.executable, str(launcher), "schema", "im", "message", "send"],
            capture_output=True,
            check=False,
            env=environment,
            text=True,
            encoding="utf-8",
            errors="strict",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        command = self.read_json(result.stdout)["data"]["commands"][0]
        self.assertEqual(command["shortcut"], "+send")
        self.assertEqual(command["subcommand"], ["message", "send"])

    def test_read_client_does_not_refresh_credentials(self):
        from wpsv7client.base import WpsV7Client

        with patch("wps_credential_manager.auto_refresh_if_expired") as refresh:
            headers = WpsV7Client(sid="sid-1")._headers()

        refresh.assert_not_called()
        self.assertEqual(headers["cookie"], "wps_sid=sid-1; csrf=sid-1")

    def test_legacy_im_recall_is_blocked(self):
        exit_code, stdout, stderr = self.invoke(["legacy", "im", "recall", "chat-1", "message-1"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("确认保护", self.read_json(stderr)["error"]["message"])

    def test_dry_run_rejects_ordinary_write_commands(self):
        exit_code, stdout, stderr = self.invoke(["im", "message", "send", "--dry-run"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("仅适用于", self.read_json(stderr)["error"]["message"])

    def test_empty_api_response_is_a_typed_network_error(self):
        with patch("wps365.handlers.wps.search_users", return_value={}):
            exit_code, stdout, stderr = self.invoke(["contact", "+search", "张三"])

        self.assertEqual(exit_code, 6)
        self.assertEqual(stdout, "")
        payload = self.read_json(stderr)
        self.assertEqual(payload["error"]["type"], "network")
        self.assertEqual(payload["error"]["subtype"], "invalid_response")

    def test_non_json_api_response_is_a_typed_network_error(self):
        response = {"code": -1, "msg": "response is not json", "text": "gateway"}
        with patch("wps365.handlers.wps.search_users", return_value=response):
            exit_code, stdout, stderr = self.invoke(["contact", "+search", "张三"])

        self.assertEqual(exit_code, 6)
        self.assertEqual(stdout, "")
        payload = self.read_json(stderr)
        self.assertEqual(payload["error"]["type"], "network")
        self.assertEqual(payload["error"]["subtype"], "invalid_response")

    def test_dbsheet_list_defaults_to_a_bounded_page(self):
        with patch("wps365.handlers.wps.dbsheet_list_records", return_value={"code": 0, "data": {"items": []}}) as list_records:
            exit_code, stdout, stderr = self.invoke(["base", "record", "list", "file-1", "2"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        list_records.assert_called_once_with("file-1", 2, page_size=20, page_token=None, filter_body=None)
        self.assertEqual(self.read_json(stdout)["data"], {"items": []})


if __name__ == "__main__":
    unittest.main()
