from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IDSecureTestCommon

MOD = "odoo.addons.hr_attendance_idsecure.models.idsecure_device.requests"


def _resp(status=200, payload=None):
    """A stand-in for requests.Response that honours raise_for_status."""
    r = MagicMock()
    r.status_code = status
    r.json.return_value = {} if payload is None else payload
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError("HTTP %s" % status)
    else:
        r.raise_for_status.return_value = None
    return r


@tagged("post_install", "-at_install")
class TestIDSecureApi(IDSecureTestCommon):
    """The appliance is mocked; tests never reach a real turnstile."""

    def test_login_stores_token(self):
        with patch(MOD + ".post", return_value=_resp(200, {"accessToken": "abc"})):
            self.assertEqual(self.device._api_login(), "abc")
        self.assertEqual(self.device.access_token, "abc")

    def test_login_invalid_credentials(self):
        with patch(MOD + ".post", return_value=_resp(401)):
            with self.assertRaises(UserError):
                self.device._api_login()

    def test_login_without_token_in_payload(self):
        with patch(MOD + ".post", return_value=_resp(200, {"foo": "bar"})):
            with self.assertRaises(UserError):
                self.device._api_login()

    def test_login_network_error(self):
        err = requests.exceptions.ConnectionError("no route")
        with patch(MOD + ".post", side_effect=err):
            with self.assertRaises(UserError):
                self.device._api_login()

    def test_headers_trigger_login_when_token_missing(self):
        self.device.access_token = False
        with patch(MOD + ".post", return_value=_resp(200, {"accessToken": "t1"})):
            headers = self.device._api_headers()
        self.assertEqual(headers["Authorization"], "Bearer t1")

    def test_headers_reuse_existing_token(self):
        self.device.access_token = "ja-tenho"
        with patch(MOD + ".post") as post:
            self.device._api_headers()
        post.assert_not_called()

    def test_get_relogs_and_retries_once_on_401(self):
        self.device.access_token = "velho"
        with patch(MOD + ".post", return_value=_resp(200, {"accessToken": "novo"})):
            with patch(
                MOD + ".get", side_effect=[_resp(401), _resp(200, {"data": []})]
            ) as get:
                out = self.device._api_get("api/x")
        self.assertEqual(get.call_count, 2)
        self.assertEqual(self.device.access_token, "novo")
        self.assertEqual(out, {"data": []})

    def test_get_without_retry_propagates_401(self):
        self.device.access_token = "velho"
        with patch(MOD + ".get", return_value=_resp(401)):
            with self.assertRaises(requests.HTTPError):
                self.device._api_get("api/x", retry=False)

    def test_get_groups_returns_payload(self):
        groups = [self._make_group(1001, "Gmar"), self._make_group(1011, "VISITAS", 1)]
        with patch.object(type(self.device), "_api_get", return_value={"data": groups}):
            out = self.device._api_get_groups()
        self.assertEqual(len(out["data"]), 2)

    def test_get_groups_swallows_errors(self):
        with patch.object(type(self.device), "_api_get", side_effect=UserError("caiu")):
            self.assertEqual(self.device._api_get_groups(), [])

    def test_report_logs_normalizes_records(self):
        payload = {
            "data": [
                {
                    "id": 5,
                    "user_id": 1001,
                    "user_name": "João da Silva (MCP)",
                    "time": "21/08/2026 11:55:12",
                    "event": "Autorizado",
                    "device_name": "CATRACA 01",
                    "area": "Área Padrão",
                }
            ]
        }
        with patch.object(type(self.device), "_api_post", return_value=payload):
            recs = self.device._api_get_report_logs()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["idUser"], 1001)
        self.assertTrue(recs[0]["_parsed_time"])

    def test_report_logs_survives_bad_timestamp(self):
        payload = {"data": [{"id": 6, "user_id": 1, "time": "não é data"}]}
        with patch.object(type(self.device), "_api_post", return_value=payload):
            recs = self.device._api_get_report_logs()
        self.assertEqual(len(recs), 1)
        self.assertFalse(recs[0]["_parsed_time"])

    def test_report_logs_empty_payload(self):
        with patch.object(type(self.device), "_api_post", return_value={}):
            self.assertEqual(self.device._api_get_report_logs(), [])

    def test_connection_failure_is_reported(self):
        with patch.object(
            type(self.device), "_api_login", side_effect=UserError("nope")
        ):
            with self.assertRaises(UserError):
                self.device.action_test_connection()

    def test_cron_skips_inactive_devices(self):
        self.device.active = False
        with patch.object(type(self.device), "action_sync_access_events") as sync:
            self.env["idsecure.device"].cron_sync_all_devices()
        sync.assert_not_called()
