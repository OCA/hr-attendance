# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime as dt

from odoo import exceptions
from odoo.tests.common import SavepointCase


class TestAttendance(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "TestEmployee",
                "tz": "Europe/Paris",
            }
        )
        # we use the default start and end limits for night work for the company: 22h to 6h
        cls.env["hr.holidays.public"].create(
            {
                "year": 2021,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Toussaint",
                            "date": "2021-11-01",
                            "variable_date": False,
                        },
                    )
                ],
            }
        )

    def _create_attendance(self, start, end=False):
        """create an attendance, start and end are in UTC"""
        return self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": start,
                "check_out": end,
            }
        )

    def test_attendance_date(self):
        attendance = self._create_attendance(
            "2021-12-02 06:00:00", "2021-12-02 15:00:00"
        )
        self.assertEqual(attendance.date, dt.date(2021, 12, 2))

    def test_attendance_date_with_tz_switch(self):
        attendance = self._create_attendance(
            "2021-12-02 23:30:00",  # this is 2021-12-03 00:30 in Europe/Paris
            "2021-12-03 08:00",
        )
        self.assertEqual(attendance.date, dt.date(2021, 12, 3))

    def test_attendance_date_type_normal(self):
        attendance = self._create_attendance(
            "2021-12-02 06:00:00", "2021-12-02 15:00:00"
        )
        self.assertEqual(attendance.date_type, "normal")

    def test_attendance_date_type_sunday(self):
        attendance = self._create_attendance(
            "2021-12-05 06:00:00", "2021-12-05 15:00:00"
        )
        self.assertEqual(attendance.date_type, "sunday")

    def test_attendance_date_type_public_holiday(self):
        attendance = self._create_attendance(
            "2021-11-01 06:00:00", "2021-11-01 15:00:00"
        )
        self.assertEqual(attendance.date_type, "holiday")

    def test_attendance_worktime_no_check_out(self):
        attendance = self._create_attendance("2021-12-02 06:00:00")
        self.assertEqual(attendance.worked_hours_nighttime, 0.0)
        self.assertEqual(attendance.worked_hours_daytime, 0.0)

    def test_attendance_worktime_just_day(self):
        attendance = self._create_attendance(
            "2021-12-02 06:00:00", "2021-12-02 15:00:00"
        )
        self.assertEqual(attendance.worked_hours_nighttime, 0.0)
        self.assertEqual(attendance.worked_hours_daytime, 9.0)

    def test_attendance_worktime_start_early(self):
        attendance = self._create_attendance(
            "2021-12-02 03:00:00", "2021-12-02 12:00:00"
        )
        self.assertEqual(attendance.worked_hours_nighttime, 2.0)
        self.assertEqual(attendance.worked_hours_daytime, 7.0)

    def test_attendance_worktime_end_late(self):
        attendance = self._create_attendance(
            "2021-12-02 15:00:00", "2021-12-03 00:00:00"
        )
        self.assertEqual(attendance.worked_hours_nighttime, 3.0)
        self.assertEqual(attendance.worked_hours_daytime, 6.0)

    def test_attendance_worktime_night_shift(self):
        attendance = self._create_attendance(
            "2021-12-02 21:00:00", "2021-12-03 06:00:00"
        )
        self.assertEqual(attendance.worked_hours_nighttime, 8.0)
        self.assertEqual(attendance.worked_hours_daytime, 1.0)

    def test_attendance_worktime_too_long(self):
        with self.assertRaises(exceptions.UserError):
            attendance = self._create_attendance(
                "2021-12-02 20:00:00", "2021-12-03 21:00:00"
            )
            # the exception happens when we flush to disk or when we read the
            # worked_hours_nighttime/daytime fields, because it is raised by
            # the computation of some fields
            attendance.flush()
