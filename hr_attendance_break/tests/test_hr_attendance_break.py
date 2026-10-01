# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from datetime import datetime, timedelta

from odoo.exceptions import UserError
from odoo.tests import common


class TestHrAttendanceBreak(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.employee = cls.env["hr.employee"].create({"name": "Break Tester"})

    def _check_in(self, check_in=None):
        return self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": check_in or datetime(2026, 1, 5, 8, 0, 0),
            }
        )

    def test_toggle_break_creates_and_closes(self):
        self._check_in()
        # Start a break
        on_break = self.employee.attendance_toggle_break()
        self.assertTrue(on_break)
        attendance = self.employee._get_open_attendance()
        self.assertEqual(len(attendance.break_ids), 1)
        self.assertTrue(attendance.is_on_break)
        self.assertFalse(attendance.break_ids.break_stop)
        # End the break
        on_break = self.employee.attendance_toggle_break()
        self.assertFalse(on_break)
        self.assertFalse(attendance.is_on_break)
        self.assertTrue(attendance.break_ids.break_stop)

    def test_multiple_breaks_sum(self):
        # A full day (08:00 -> 17:00) with three breaks.
        attendance = self._check_in()
        attendance.check_out = datetime(2026, 1, 5, 17, 0, 0)
        # Three closed breaks of 15, 30 and 15 minutes = 1.0 h total.
        base = datetime(2026, 1, 5, 10, 0, 0)
        for start_offset, minutes in ((0, 15), (150, 30), (300, 15)):
            start = base + timedelta(minutes=start_offset)
            self.env["hr.attendance.break"].create(
                {
                    "attendance_id": attendance.id,
                    "break_start": start,
                    "break_stop": start + timedelta(minutes=minutes),
                }
            )
        self.assertEqual(len(attendance.break_ids), 3)
        self.assertAlmostEqual(attendance.break_hours, 1.0, places=2)
        # The module's guarantee: net worked = worked - breaks.
        self.assertGreater(attendance.worked_hours, 1.0)
        self.assertAlmostEqual(
            attendance.net_worked_hours,
            attendance.worked_hours - 1.0,
            places=2,
        )

    def test_auto_close_break_on_checkout(self):
        self._check_in()
        self.employee.attendance_toggle_break()
        attendance = self.employee._get_open_attendance()
        self.assertTrue(attendance.is_on_break)
        # Checking out must auto-close the running break.
        self.employee._attendance_action_change()
        self.assertTrue(attendance.check_out)
        self.assertTrue(attendance.break_ids.break_stop)
        self.assertFalse(attendance.is_on_break)

    def test_rounding(self):
        attendance = self._check_in()
        vals = {
            "attendance_id": attendance.id,
            "break_start": datetime(2026, 1, 5, 10, 0, 0),
            "break_stop": datetime(2026, 1, 5, 10, 12, 0),
        }
        # No rounding -> exact 12 minutes (0.2 h).
        self.company.attendance_break_rounding_minutes = 0
        rec = self.env["hr.attendance.break"].create(vals)
        self.assertAlmostEqual(rec.duration, 0.2, places=2)
        # Round to nearest 15 minutes -> 12 minutes becomes 0.25 h.
        self.company.attendance_break_rounding_minutes = 15
        rec.invalidate_recordset(["duration"])
        self.assertAlmostEqual(rec.duration, 0.25, places=2)

    def test_toggle_break_requires_checkin(self):
        # No open attendance -> cannot record a break.
        with self.assertRaises(UserError):
            self.employee.attendance_toggle_break()
