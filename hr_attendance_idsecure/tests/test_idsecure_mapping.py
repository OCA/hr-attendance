from datetime import datetime
from unittest.mock import patch

from odoo.tests.common import tagged

from .common import IDSecureTestCommon


@tagged("post_install", "-at_install")
class TestIDSecureMapping(IDSecureTestCommon):
    """Company mapping, import filtering and event dispatch."""

    def test_statistics_count_events(self):
        self.env["idsecure.access.log"].create(
            {
                "device_id": self.device.id,
                "id_log": 90001,
                "employee_name_raw": "X",
                "id_user": 1,
                "event_time": datetime.now(),
                "direction": "entry",
                "state": "error",
            }
        )
        self.device.invalidate_recordset()
        self.assertGreaterEqual(self.device.total_events, 1)
        self.assertGreaterEqual(self.device.failed_events, 1)

    def test_user_mapping_without_id_returns_nothing(self):
        self.assertEqual(self.device._get_user_mapping(0), (False, None))

    def test_user_mapping_resolves_group(self):
        user = self._make_user_api_response(
            1001, "João", [self._make_group(1012, "MCP", 2)]
        )
        with patch.object(type(self.device), "_api_get_user", return_value=user):
            mapping, data = self.device._get_user_mapping(1001)
        self.assertEqual(mapping, self.mapping_mcp)
        self.assertTrue(data)

    def test_user_mapping_unknown_group(self):
        user = self._make_user_api_response(
            7777, "Estranho", [self._make_group(999999, "Nada", 2)]
        )
        with patch.object(type(self.device), "_api_get_user", return_value=user):
            mapping, _data = self.device._get_user_mapping(7777)
        self.assertFalse(mapping)

    def test_should_import_without_mappings_imports_all(self):
        self.device.mapping_ids.unlink()
        allowed = self.device._should_import(1001)[0]
        self.assertTrue(allowed)

    def test_should_import_respects_visitor_flag(self):
        user = self._make_user_api_response(
            2001, "Visitante", [self._make_group(1011, "VISITAS", 1)]
        )
        with patch.object(type(self.device), "_api_get_user", return_value=user):
            allowed = self.device._should_import(2001)[0]
        self.assertFalse(allowed, "grupo VISITAS tem import_attendance=False")

    def test_should_import_allows_mapped_company(self):
        user = self._make_user_api_response(
            1001, "João", [self._make_group(1012, "MCP", 2)]
        )
        with patch.object(type(self.device), "_api_get_user", return_value=user):
            allowed, etype, company = self.device._should_import(1001)
        self.assertTrue(allowed)
        self.assertEqual(etype, "employee")
        self.assertEqual(company, self.company.id)

    def test_find_employee_prefers_idsecure_id_over_name(self):
        """The numeric id wins even when the name points somewhere else."""
        emp = self.device._find_employee(self._make_raw_event(1, "Ana Costa", 1001))
        self.assertEqual(emp, self.employee_mcp)

    def test_sync_creates_logs_from_report(self):
        raw = [
            {
                "idLog": 0,
                "idUser": 1001,
                "name": "João da Silva (MCP)",
                "time": "21/08/2026 08:00:00",
                "_parsed_time": datetime(2026, 8, 21, 8, 0, 0),
                "eventCode": 0,
                "eventName": "Autorizado",
                "device": "catraca 1",
                "area": "Área Padrão",
                "info": "",
            }
        ]
        before = self.env["idsecure.access.log"].search_count([])
        with patch.object(
            type(self.device), "_api_get_report_logs", return_value=raw
        ), patch.object(
            type(self.device),
            "_should_import",
            return_value=(True, "employee", self.company.id),
        ):
            self.device.action_sync_access_events()
        self.assertGreater(self.env["idsecure.access.log"].search_count([]), before)

    def test_sync_updates_last_sync(self):
        with patch.object(type(self.device), "_api_get_report_logs", return_value=[]):
            self.device.action_sync_access_events()
        self.assertTrue(self.device.last_sync)

    def test_sync_propagates_appliance_failure(self):
        with patch.object(
            type(self.device),
            "_api_get_report_logs",
            side_effect=Exception("appliance mudo"),
        ):
            with self.assertRaisesRegex(Exception, "appliance mudo"):
                self.device.action_sync_access_events()

    def test_cron_syncs_active_device(self):
        with patch.object(type(self.device), "action_sync_access_events") as sync:
            self.env["idsecure.device"].cron_sync_all_devices()
        sync.assert_called()


@tagged("post_install", "-at_install")
class TestIDSecureDuplicateDetection(IDSecureTestCommon):
    """Odoo's own overlap errors are not iDSecure failures."""

    def _log(self):
        return self.env["idsecure.access.log"].create(
            {
                "device_id": self.device.id,
                "id_log": 91001,
                "employee_id": self.employee_mcp.id,
                "employee_name_raw": self.employee_mcp.name,
                "id_user": 1001,
                "event_time": datetime.now(),
                "direction": "entry",
                "state": "pending",
            }
        )

    def test_overlap_messages_are_treated_as_duplicates(self):
        log = self._log()
        for msg in (
            "Cannot create new attendance",
            "o funcionário já bateu sua Entrada",
            "already has an attendance",
            "Não é possível criar",
            "attendance overlap detected",
        ):
            self.assertTrue(log._is_duplicate_error(msg), msg)

    def test_real_absence_error_is_not_a_duplicate(self):
        log = self._log()
        self.assertFalse(
            log._is_duplicate_error("O funcionário não comparece ao trabalho hoje")
        )

    def test_unrelated_error_is_not_a_duplicate(self):
        log = self._log()
        self.assertFalse(log._is_duplicate_error("conexão recusada pelo banco"))
