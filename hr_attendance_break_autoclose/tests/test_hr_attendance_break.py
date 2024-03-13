# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import datetime

from odoo.addons.hr_attendance_break.tests.test_hr_attendance_break import (
    TestHrAttendance as _TestHrAttendance,
)


class TestHrAttendanceAutoclose(_TestHrAttendance):
    def test_open_worked_hours(self):
        """Test that we subtract breaks from open work hours"""
        self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 8, 0, 0)
        self.assertEqual(self.attendance.open_worked_hours, 9.5)
