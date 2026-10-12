from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged

from .common import IDSecureTestCommon


@tagged("post_install", "-at_install")
class TestIDSecureWizards(IDSecureTestCommon):
    def _pending_log(self, name, id_user, id_log):
        return self.env["idsecure.access.log"].create(
            {
                "device_id": self.device.id,
                "id_log": id_log,
                "employee_name_raw": name,
                "id_user": id_user,
                "event_time": datetime.now(),
                "direction": "entry",
                "event_code": 7,
                "event_name": "Test",
                "state": "no_employee",
            }
        )

    # ---------------- wizard de vinculo ----------------

    def test_sync_wizard_lists_unmatched_users(self):
        self._pending_log("Fulano Desconhecido", 5001, 80001)
        self._pending_log("Fulano Desconhecido", 5001, 80002)
        self._pending_log("Outro Sujeito", 5002, 80003)
        wiz = self.env["idsecure.sync.wizard"].create({})
        users = wiz.line_ids.mapped("id_user")
        self.assertIn(5001, users)
        self.assertIn(5002, users)
        self.assertEqual(len(users), len(set(users)), "sem duplicar id_user")

    def test_sync_wizard_counts_pending_events(self):
        self._pending_log("Repetido", 5003, 80004)
        self._pending_log("Repetido", 5003, 80005)
        wiz = self.env["idsecure.sync.wizard"].create({})
        line = wiz.line_ids.filtered(lambda x: x.id_user == 5003)
        self.assertEqual(line.pending_count, 2)

    def test_sync_wizard_suggests_employee_by_name(self):
        self._pending_log("João da Silva (MCP)", 5004, 80006)
        wiz = self.env["idsecure.sync.wizard"].create({})
        line = wiz.line_ids.filtered(lambda x: x.id_user == 5004)
        self.assertEqual(line.employee_id, self.employee_mcp)

    def test_sync_wizard_apply_links_and_reprocesses(self):
        log = self._pending_log("Ninguem Conhecido", 5005, 80007)
        wiz = self.env["idsecure.sync.wizard"].create({})
        line = wiz.line_ids.filtered(lambda x: x.id_user == 5005)
        line.employee_id = self.employee_no_idsecure
        wiz.action_apply()
        self.assertEqual(self.employee_no_idsecure.idsecure_id, 5005)
        self.assertNotEqual(log.state, "no_employee")

    def test_sync_wizard_apply_ignores_lines_without_employee(self):
        self._pending_log("Sem Par", 5006, 80008)
        wiz = self.env["idsecure.sync.wizard"].create({})
        wiz.line_ids.filtered(lambda x: x.id_user == 5006).employee_id = False
        wiz.action_apply()  # nao deve levantar

    # ---------------- wizard historico ----------------

    def test_historical_wizard_rejects_inverted_range(self):
        with self.assertRaises(ValidationError):
            self.env["idsecure.historical.sync.wizard"].create(
                {
                    "device_id": self.device.id,
                    "date_from": datetime.now(),
                    "date_to": datetime.now() - timedelta(days=1),
                }
            )

    def test_historical_wizard_calls_sync_with_range(self):
        d_from = datetime.now() - timedelta(days=2)
        d_to = datetime.now()
        wiz = self.env["idsecure.historical.sync.wizard"].create(
            {"device_id": self.device.id, "date_from": d_from, "date_to": d_to}
        )
        with patch.object(
            type(self.device), "action_sync_access_events", return_value=None
        ) as sync:
            wiz.action_sync()
        sync.assert_called_once()

    def test_historical_wizard_propagates_device_error(self):
        wiz = self.env["idsecure.historical.sync.wizard"].create(
            {
                "device_id": self.device.id,
                "date_from": datetime.now() - timedelta(days=1),
                "date_to": datetime.now(),
            }
        )
        with patch.object(
            type(self.device),
            "action_sync_access_events",
            side_effect=UserError("appliance fora do ar"),
        ):
            with self.assertRaises(UserError):
                wiz.action_sync()
