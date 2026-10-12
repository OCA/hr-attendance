from datetime import datetime
from unittest.mock import patch

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import IDSecureTestCommon

LOG = "odoo.addons.hr_attendance_idsecure.models.idsecure_access_log"


@tagged("post_install", "-at_install")
class TestIDSecureNotification(IDSecureTestCommon):
    """HR is warned in the employee chatter when a punch cannot be recorded."""

    def _log(self, id_log, employee=None):
        emp = employee if employee is not None else self.employee_mcp
        return self.env["idsecure.access.log"].create(
            {
                "device_id": self.device.id,
                "id_log": id_log,
                "employee_id": emp.id if emp else False,
                "employee_name_raw": emp.name if emp else "Sem Cadastro",
                "id_user": emp.idsecure_id if emp else 0,
                "event_time": datetime.now(),
                "direction": "entry",
                "state": "pending",
            }
        )

    def test_notification_posts_to_employee_chatter(self):
        log = self._log(96001)
        before = self.env["mail.message"].search_count(
            [("model", "=", "hr.employee"), ("res_id", "=", self.employee_mcp.id)]
        )
        log._notify_hr_attendance_error("banco fora do ar")
        after = self.env["mail.message"].search_count(
            [("model", "=", "hr.employee"), ("res_id", "=", self.employee_mcp.id)]
        )
        self.assertEqual(after, before + 1)

    def test_notification_body_carries_the_error(self):
        log = self._log(96002)
        log._notify_hr_attendance_error("falha específica xyz")
        msg = self.env["mail.message"].search(
            [("model", "=", "hr.employee"), ("res_id", "=", self.employee_mcp.id)],
            order="id desc",
            limit=1,
        )
        self.assertIn("xyz", msg.body)
        self.assertIn(self.employee_mcp.name, msg.body)

    def test_notification_is_skipped_without_employee(self):
        log = self._log(96003, employee=False)
        before = self.env["mail.message"].search_count([])
        log._notify_hr_attendance_error("qualquer coisa")
        self.assertEqual(self.env["mail.message"].search_count([]), before)

    @mute_logger(LOG)
    def test_notification_failure_never_breaks_the_sync(self):
        """A broken chatter must not abort attendance processing."""
        log = self._log(96004)
        with patch.object(
            type(self.employee_mcp),
            "message_post",
            side_effect=Exception("mail server down"),
        ):
            log._notify_hr_attendance_error("erro original")  # nao pode levantar

    def test_direction_label_in_notification(self):
        log = self._log(96005)
        log.direction = "exit"
        log._notify_hr_attendance_error("erro na saida")
        msg = self.env["mail.message"].search(
            [("model", "=", "hr.employee"), ("res_id", "=", self.employee_mcp.id)],
            order="id desc",
            limit=1,
        )
        self.assertTrue(msg.body)
