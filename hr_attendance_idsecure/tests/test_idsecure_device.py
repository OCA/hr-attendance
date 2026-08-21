from datetime import datetime
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import tagged

from .common import IDSecureTestCommon


@tagged("post_install", "-at_install")
class TestIDSecureDevice(IDSecureTestCommon):
    def test_create_device(self):
        self.assertEqual(self.device.state, "draft")
        self.assertTrue(self.device.active)

    def test_base_url_validation(self):
        with self.assertRaises(ValidationError):
            self.env["idsecure.device"].create(
                {
                    "name": "Bad",
                    "base_url": "ftp://bad",
                    "username": "a",
                    "password": "test",
                }
            )

    def test_get_base_url_trailing_slash(self):
        self.device.base_url = "https://test.local"
        self.assertEqual(self.device._get_base_url(), "https://test.local/")

    def test_parse_dotnet_time_with_offset(self):
        dt = self.device._parse_dotnet_time("/Date(1766009913000-0300)/")
        self.assertIsInstance(dt, datetime)
        self.assertIsNone(dt.tzinfo)

    def test_parse_dotnet_time_empty(self):
        self.assertFalse(self.device._parse_dotnet_time(""))
        self.assertFalse(self.device._parse_dotnet_time(None))

    def test_detect_direction_entrada(self):
        self.assertEqual(self.device._detect_direction("Entrada", ""), "entry")

    def test_detect_direction_saida(self):
        self.assertEqual(self.device._detect_direction("Saída", ""), "exit")

    def test_detect_direction_unknown(self):
        self.assertFalse(self.device._detect_direction("", ""))

    def test_find_employee_by_idsecure_id(self):
        emp = self.device._find_employee(
            self._make_raw_event(1, "João da Silva (MCP)", 1001)
        )
        self.assertEqual(emp, self.employee_mcp)

    def test_find_employee_by_name(self):
        emp = self.device._find_employee(self._make_raw_event(1, "Ana Costa", 9999))
        self.assertEqual(emp, self.employee_no_idsecure)

    def test_find_employee_not_found(self):
        emp = self.device._find_employee(self._make_raw_event(1, "Nobody", 9999))
        self.assertFalse(emp)

    def test_should_import_mcp(self):
        with patch.object(type(self.device), "_api_get_user") as m:
            m.return_value = self._make_user_api_response(
                1001, "João", [self._make_group(1012, "MCP", 2)]
            )
            s, t, c = self.device._should_import(1001)
            self.assertTrue(s)
            self.assertEqual(t, "employee")

    def test_should_import_freelancer(self):
        with patch.object(type(self.device), "_api_get_user") as m:
            m.return_value = self._make_user_api_response(
                1003, "Pedro", [self._make_group(1001, "Gmar", 2)]
            )
            s, t, c = self.device._should_import(1003)
            self.assertTrue(s)
            self.assertEqual(t, "freelancer")

    def test_should_not_import_visitors(self):
        with patch.object(type(self.device), "_api_get_user") as m:
            m.return_value = self._make_user_api_response(
                5000, "Visitor", [self._make_group(1011, "VISITAS", 1)]
            )
            s, t, c = self.device._should_import(5000)
            self.assertFalse(s)

    def test_should_import_no_mappings(self):
        self.device.mapping_ids.unlink()
        s, t, c = self.device._should_import(1001)
        self.assertTrue(s)

    def test_sync_creates_log(self):
        self.device.mapping_ids.unlink()
        with patch.object(type(self.device), "_api_get_access_logs") as m:
            m.return_value = [
                self._make_raw_event(50001, "João da Silva (MCP)", 1001, "Entrada")
            ]
            self.device.state = "connected"
            self.device.action_sync_access_events()
        log = self.env["idsecure.access.log"].search(
            [("device_id", "=", self.device.id), ("id_log", "=", 50001)]
        )
        self.assertTrue(log)
        self.assertEqual(log.employee_id, self.employee_mcp)

    def test_sync_deduplicates(self):
        self.device.mapping_ids.unlink()
        with patch.object(type(self.device), "_api_get_access_logs") as m:
            m.return_value = [self._make_raw_event(50002, "João da Silva (MCP)", 1001)]
            self.device.state = "connected"
            self.device.action_sync_access_events()
            self.device.action_sync_access_events()
        self.assertEqual(
            len(
                self.env["idsecure.access.log"].search(
                    [("device_id", "=", self.device.id), ("id_log", "=", 50002)]
                )
            ),
            1,
        )

    def test_sync_filters_visitors(self):
        with patch.object(
            type(self.device), "_api_get_access_logs"
        ) as ml, patch.object(type(self.device), "_api_get_user") as mu:
            ml.return_value = [self._make_raw_event(50003, "Visitor", 5000)]
            mu.return_value = self._make_user_api_response(
                5000, "Visitor", [self._make_group(1011, "VISITAS", 1)]
            )
            self.device.state = "connected"
            self.device.action_sync_access_events()
        self.assertFalse(
            self.env["idsecure.access.log"].search(
                [("device_id", "=", self.device.id), ("id_log", "=", 50003)]
            )
        )

    def test_load_mappings(self):
        self.device.mapping_ids.unlink()
        with patch.object(type(self.device), "_api_get_groups") as m:
            m.return_value = {
                "data": [
                    {"id": 2001, "name": "TestCo", "idType": 2},
                    {"id": 2002, "name": "VISITAS", "idType": 1},
                ]
            }
            self.device.state = "connected"
            self.device.action_load_mappings()
        self.assertEqual(len(self.device.mapping_ids), 2)
        self.assertFalse(
            self.device.mapping_ids.filtered(
                lambda m: m.name == "VISITAS"
            ).import_attendance
        )

    def test_load_mappings_no_dupes(self):
        with patch.object(type(self.device), "_api_get_groups") as m:
            m.return_value = {"data": [{"id": 1012, "name": "MCP", "idType": 2}]}
            n = len(self.device.mapping_ids)
            self.device.state = "connected"
            self.device.action_load_mappings()
        self.assertEqual(len(self.device.mapping_ids), n)
