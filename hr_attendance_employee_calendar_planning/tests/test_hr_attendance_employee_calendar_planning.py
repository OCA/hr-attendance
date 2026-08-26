# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestHrAttendanceEmployeeCalendarPlanning(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Test calendar 1",
                "attendance_ids": [],
                "tz": "UTC",
                "stored_flexible_hours": True,
                "stored_full_time_required_hours": 20,
                "stored_hours_per_day": 4,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test employee",
                "calendar_ids": [
                    Command.create(
                        {"date_end": "2026-12-31", "calendar_id": cls.calendar.id}
                    ),
                ],
            }
        )

    @mute_logger("odoo.models.unlink")
    def test_update_overtime(self):
        attendance = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": "2026-01-01 08:00:00",
            }
        )
        self.assertEqual(attendance.worked_hours, 0)
        self.assertEqual(attendance.overtime_hours, 0)
        attendance.write(
            {
                "check_out": "2026-01-01 10:00:00",
            }
        )
        self.assertEqual(attendance.worked_hours, 2)
        self.assertEqual(attendance.overtime_hours, -2)
        attendance.unlink()
        attendance_extra = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": "2026-01-01 06:00:00",
                "check_out": "2026-01-01 12:00:00",
            }
        )
        self.assertEqual(attendance_extra.worked_hours, 6)
        self.assertAlmostEqual(attendance_extra.overtime_hours, 2)
