from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import IDSecureTestCommon

LOG = "odoo.addons.hr_attendance_idsecure.models.idsecure_access_log"


@tagged("post_install", "-at_install")
class TestIDSecureErrorHandling(IDSecureTestCommon):
    def _log(self, employee=None, direction="entry", id_log=95001, state="pending"):
        return self.env["idsecure.access.log"].create(
            {
                "device_id": self.device.id,
                "id_log": id_log,
                "employee_id": (employee or self.employee_mcp).id,
                "employee_name_raw": (employee or self.employee_mcp).name,
                "id_user": (employee or self.employee_mcp).idsecure_id,
                "event_time": datetime.now(),
                "direction": direction,
                "info": "Entrada" if direction == "entry" else "Saída",
                "state": state,
            }
        )

    @mute_logger(LOG)
    def test_duplicate_error_is_swallowed_as_done(self):
        """Odoo's own overlap error is not an integration failure."""
        log = self._log(id_log=95001)
        with patch.object(
            type(log), "_do_check_in", side_effect=Exception("o funcionário já bateu")
        ):
            log._process_attendance()
        self.assertEqual(log.state, "done")
        self.assertFalse(log.error_message)

    @mute_logger(LOG)
    def test_real_error_is_recorded_and_notified(self):
        log = self._log(id_log=95002)
        with patch.object(
            type(log), "_do_check_in", side_effect=Exception("banco indisponível")
        ), patch.object(type(log), "_notify_hr_attendance_error") as notify:
            log._process_attendance()
        self.assertEqual(log.state, "error")
        self.assertIn("banco", log.error_message)
        notify.assert_called_once()

    @mute_logger(LOG)
    def test_error_message_is_truncated(self):
        log = self._log(id_log=95003)
        with patch.object(
            type(log), "_do_check_in", side_effect=Exception("x" * 900)
        ), patch.object(type(log), "_notify_hr_attendance_error"):
            log._process_attendance()
        self.assertLessEqual(len(log.error_message), 500)

    def test_retry_rematches_missing_employee(self):
        """action_retry must try to link the employee again before processing."""
        log = self._log(id_log=95004, state="no_employee")
        log.employee_id = False
        log.employee_name_raw = "Ana Costa"
        log.id_user = 0
        log.action_retry()
        self.assertEqual(log.employee_id, self.employee_no_idsecure)

    def test_retry_without_any_match_stays_unlinked(self):
        log = self._log(id_log=95005, state="no_employee")
        log.employee_id = False
        log.employee_name_raw = "Fantasma Inexistente"
        log.id_user = 0
        log.action_retry()
        self.assertFalse(log.employee_id)

    def test_processing_skips_when_no_employee(self):
        log = self._log(id_log=95006)
        log.employee_id = False
        log._process_attendance()
        self.assertNotEqual(log.state, "done")

    def test_check_in_then_check_out_pairs_up(self):
        t1 = datetime.now() - timedelta(days=9, hours=3)
        i = self._log(self.employee_rm, "entry", 95007)
        i.event_time = t1
        i._process_attendance()
        o = self._log(self.employee_rm, "exit", 95008)
        o.event_time = t1 + timedelta(hours=2)
        o._process_attendance()
        self.assertEqual(o.state, "done")
        self.assertEqual(i.attendance_id, o.attendance_id)
        self.assertTrue(o.attendance_id.check_out)
