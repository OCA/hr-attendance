from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import requests

from odoo.tests.common import tagged

from .common import IDSecureTestCommon

MOD = "odoo.addons.hr_attendance_idsecure.models.idsecure_device.requests"


def _resp(status=200, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = {} if payload is None else payload
    r.raise_for_status.side_effect = (
        requests.HTTPError("HTTP %s" % status) if status >= 400 else None
    )
    return r


@tagged("post_install", "-at_install")
class TestIDSecureEndpointChoice(IDSecureTestCommon):
    """Monitor endpoint for live polling, report endpoint for history."""

    def test_post_retries_once_on_401(self):
        self.device.access_token = "velho"
        with patch(MOD + ".post") as post:
            post.side_effect = [
                _resp(401),
                _resp(200, {"accessToken": "novo"}),
                _resp(200, {"data": [{"id": 1}]}),
            ]
            out = self.device._api_post("api/x", json_body={})
        self.assertEqual(out, {"data": [{"id": 1}]})

    def test_post_without_retry_propagates(self):
        self.device.access_token = "t"
        with patch(MOD + ".post", return_value=_resp(500)):
            with self.assertRaises(requests.HTTPError):
                self.device._api_post("api/x", retry=False)

    def test_live_poll_uses_monitor_endpoint(self):
        with patch.object(
            type(self.device), "_api_get", return_value={"data": [{"idLog": 1}]}
        ) as api_get:
            out = self.device._api_get_access_logs(limit=10)
        self.assertEqual(len(out), 1)
        self.assertIn("monitor", api_get.call_args[0][0])

    def test_date_range_uses_report_endpoint(self):
        with patch.object(
            type(self.device), "_api_get_report_logs", return_value=[]
        ) as rep:
            self.device._api_get_access_logs(
                limit=10, initial_date=datetime.now() - timedelta(days=1)
            )
        rep.assert_called_once()

    def test_monitor_endpoint_empty_payload(self):
        with patch.object(type(self.device), "_api_get", return_value={}):
            self.assertEqual(self.device._api_get_access_logs(), [])

    def test_base_url_normalisation(self):
        for given in ("https://a.local", "https://a.local/"):
            self.device.base_url = given
            self.assertTrue(self.device._get_base_url().endswith("/"))

    def test_get_user_handles_api_failure(self):
        with patch.object(
            type(self.device), "_api_get", side_effect=requests.HTTPError("500")
        ):
            self.assertFalse(self.device._api_get_user(1))

    def test_detect_direction_variants(self):
        self.assertEqual(self.device._detect_direction("ENTRADA liberada", ""), "entry")
        self.assertEqual(self.device._detect_direction("SAIDA liberada", ""), "exit")
        self.assertEqual(self.device._detect_direction("", "Saída"), "exit")
        self.assertFalse(self.device._detect_direction("qualquer coisa", "Autorizado"))

    def test_find_employee_without_match(self):
        self.assertFalse(
            self.device._find_employee(self._make_raw_event(1, "Ninguém Aqui", 987654))
        )

    def test_find_employee_ignores_blank_name(self):
        self.assertFalse(self.device._find_employee({"name": "", "idUser": 0}))

    def test_load_mappings_creates_records(self):
        groups = [self._make_group(2222, "NOVA EMPRESA", 2)]
        before = self.env["idsecure.company.mapping"].search_count(
            [("device_id", "=", self.device.id)]
        )
        with patch.object(
            type(self.device), "_api_get_groups", return_value={"data": groups}
        ):
            self.device.action_load_mappings()
        after = self.env["idsecure.company.mapping"].search_count(
            [("device_id", "=", self.device.id)]
        )
        self.assertGreater(after, before)

    def test_load_mappings_is_idempotent(self):
        groups = [self._make_group(1012, "MCP", 2)]
        with patch.object(
            type(self.device), "_api_get_groups", return_value={"data": groups}
        ):
            self.device.action_load_mappings()
            n1 = self.env["idsecure.company.mapping"].search_count(
                [("device_id", "=", self.device.id)]
            )
            self.device.action_load_mappings()
            n2 = self.env["idsecure.company.mapping"].search_count(
                [("device_id", "=", self.device.id)]
            )
        self.assertEqual(n1, n2)


@tagged("post_install", "-at_install")
class TestIDSecureLookupAndFilters(IDSecureTestCommon):
    """Date filters on the report query and employee lookup fallbacks."""

    def test_report_query_carries_the_date_range(self):
        captured = {}

        def fake_post(endpoint, params=None, json_body=None, retry=True):
            captured["params"] = params
            return {"data": []}

        with patch.object(type(self.device), "_api_post", side_effect=fake_post):
            self.device._api_get_report_logs(
                initial_date=datetime(2026, 3, 1), final_date=datetime(2026, 3, 31)
            )
        self.assertEqual(captured["params"]["initialDate"], "2026-03-01")
        self.assertEqual(captured["params"]["finalDate"], "2026-03-31")

    def test_report_query_without_dates_omits_them(self):
        captured = {}

        def fake_post(endpoint, params=None, json_body=None, retry=True):
            captured["params"] = params
            return {"data": []}

        with patch.object(type(self.device), "_api_post", side_effect=fake_post):
            self.device._api_get_report_logs()
        self.assertNotIn("initialDate", captured["params"])
        self.assertNotIn("finalDate", captured["params"])

    def test_partner_group_becomes_freelancer(self):
        payload = {"data": [self._make_group(4444, "EMPRESAS PARCEIRAS", 1)]}
        with patch.object(type(self.device), "_api_get_groups", return_value=payload):
            self.device.action_load_mappings()
        mapping = self.env["idsecure.company.mapping"].search(
            [("device_id", "=", self.device.id), ("idsecure_group_id", "=", 4444)],
            limit=1,
        )
        self.assertEqual(mapping.employee_type, "freelancer")

    def test_mapping_with_import_disabled_blocks_user(self):
        user = self._make_user_api_response(
            5555, "Bloqueado", [self._make_group(1011, "VISITAS", 1)]
        )
        with patch.object(type(self.device), "_api_get_user", return_value=user):
            self.assertEqual(self.device._should_import(5555), (False, None, None))

    def test_find_employee_by_badge_number(self):
        self.employee_freelancer.barcode = "CRACHA123"
        emp = self.device._find_employee(
            {"idUser": 0, "cardNumberStr": "CRACHA123", "name": ""}
        )
        self.assertEqual(emp, self.employee_freelancer)

    def test_find_employee_partial_name_match(self):
        """A partial name still matches, but the module warns to set the id."""
        emp = self.device._find_employee(
            {"idUser": 0, "cardNumberStr": "", "name": "Maria Santos (RM)"}
        )
        self.assertEqual(emp, self.employee_rm)
