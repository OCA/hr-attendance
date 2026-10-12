from datetime import datetime, timedelta

from psycopg2 import IntegrityError

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import IDSecureTestCommon


@tagged("post_install", "-at_install")
class TestIDSecureAccessLog(IDSecureTestCommon):
    def _create_log(
        self,
        employee,
        direction="entry",
        event_time=None,
        id_log=None,
        state="pending",
        info="",
    ):
        if event_time is None:
            event_time = datetime.now()
        if id_log is None:
            id_log = int(datetime.now().timestamp() * 1000) % 2147483647
        return self.env["idsecure.access.log"].create(
            {
                "device_id": self.device.id,
                "id_log": id_log,
                "employee_id": employee.id if employee else False,
                "employee_name_raw": employee.name if employee else "Unknown",
                "id_user": employee.idsecure_id if employee else 0,
                "event_time": event_time,
                "direction": direction,
                "event_code": 7,
                "event_name": "Test",
                "device_name": "catraca 1",
                "area_name": "Test",
                "info": info,
                "state": state,
            }
        )

    def test_check_in_creates_attendance(self):
        now = datetime.now()
        log = self._create_log(self.employee_mcp, "entry", now)
        log._process_attendance()
        self.assertEqual(log.state, "done")
        self.assertTrue(log.attendance_id)
        self.assertEqual(log.attendance_id.check_in, now)

    def test_check_out_closes_attendance(self):
        t1 = datetime.now() - timedelta(hours=8)
        t2 = datetime.now()
        li = self._create_log(self.employee_mcp, "entry", t1, id_log=70001)
        li._process_attendance()
        lo = self._create_log(self.employee_mcp, "exit", t2, id_log=70002)
        lo._process_attendance()
        self.assertEqual(lo.state, "done")
        self.assertEqual(lo.attendance_id.check_out, t2)

    def test_check_out_without_checkin_is_error(self):
        """A reliable exit with no open attendance must fail, not be inferred."""
        log = self._create_log(
            self.employee_rm, "exit", datetime.now(), id_log=70003, info="Saída"
        )
        self.assertTrue(log._has_reliable_direction())
        log._process_attendance()
        self.assertEqual(log.state, "error")
        self.assertFalse(log.attendance_id)

    def test_unreliable_exit_is_inferred_as_entry(self):
        """Without usable info the direction is toggled from the open shift."""
        log = self._create_log(self.employee_rm, "exit", datetime.now(), id_log=70014)
        self.assertFalse(log._has_reliable_direction())
        log._process_attendance()
        self.assertEqual(log.direction, "entry")
        self.assertEqual(log.state, "done")

    def test_unreliable_direction_toggles_to_exit(self):
        """With a shift already open the same event becomes a check-out."""
        t1 = datetime.now() - timedelta(days=11, hours=2)
        self._create_log(
            self.employee_freelancer, "entry", t1, id_log=70005
        )._process_attendance()
        log = self._create_log(
            self.employee_freelancer,
            "entry",
            t1 + timedelta(hours=1),
            id_log=70006,
        )
        log._process_attendance()
        self.assertEqual(log.direction, "exit")
        self.assertEqual(log.state, "done")

    def test_no_employee_marks_state(self):
        log = self._create_log(None, "entry", datetime.now(), id_log=70004)
        log.employee_id = False
        log._process_attendance()
        self.assertEqual(log.state, "no_employee")

    def test_unique_constraint(self):
        self._create_log(self.employee_mcp, "entry", datetime.now(), id_log=70010)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            with self.cr.savepoint():
                self._create_log(
                    self.employee_mcp, "entry", datetime.now(), id_log=70010
                )

    def test_report_records_share_id_log_zero(self):
        """The report endpoint has no idLog, so id_log=0 must not be unique."""
        a = self._create_log(self.employee_mcp, "entry", datetime.now(), id_log=0)
        b = self._create_log(self.employee_rm, "entry", datetime.now(), id_log=0)
        self.assertTrue(a and b)
        self.assertNotEqual(a, b)

    def test_retry(self):
        now = datetime.now()
        li = self._create_log(
            self.employee_rm, "entry", now - timedelta(hours=1), id_log=70020
        )
        li._process_attendance()
        lo = self._create_log(self.employee_rm, "exit", now, id_log=70021)
        lo.write({"state": "error", "error_message": "Test"})
        lo.action_retry()
        self.assertEqual(lo.state, "done")
