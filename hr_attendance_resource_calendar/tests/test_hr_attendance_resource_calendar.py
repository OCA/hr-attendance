# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from unittest.mock import patch

import pytz

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestHrEmployeeAttendance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CalendarAttendance = cls.env["resource.calendar.attendance"]
        cls.HrAttendance = cls.env["hr.attendance"]
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Calendario prueba",
                "tz": "UTC",
                "attendance_before": 0.25,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Employee test",
                "resource_calendar_id": cls.calendar.id,
            }
        )
        cls.calendar_attendance_values = {
            "name": "Calendar attendance test",
            "calendar_id": cls.calendar.id,
            "day_period": "morning",
        }

    def _current_day_and_hour(self):
        tz = pytz.timezone(self.calendar.tz or "UTC")
        now = datetime.now(tz)
        float_hour = now.hour + now.minute / 60.0 + now.second / 3600.0
        return str(now.weekday()), float_hour

    def test_no_attendance_lines(self):
        self.CalendarAttendance.search(
            [("calendar_id", "=", self.calendar.id)]
        ).unlink()
        with self.assertRaises(UserError):
            self.employee._valid_attendance_working_hours()

    def test_within_working_hours(self):
        day, hour = self._current_day_and_hour()
        start = max(hour - 0.5, 0.0)
        end = min(hour + 0.5, 23.99)
        if start >= end:
            start = max(hour - 0.25, 0.0)
            end = start + 0.5
        self.calendar_attendance_values.update(
            {
                "dayofweek": day,
                "hour_from": start,
                "hour_to": end,
            }
        )
        self.CalendarAttendance.create(self.calendar_attendance_values)
        self.employee._valid_attendance_working_hours()

    def test_before_working_hours_with_margin(self):
        day, hour = self._current_day_and_hour()
        start = min(hour + 0.1, 23.5)
        end = min(start + 1.0, 23.99)
        self.calendar_attendance_values.update(
            {
                "dayofweek": day,
                "hour_from": start,
                "hour_to": end,
            }
        )
        self.CalendarAttendance.create(self.calendar_attendance_values)
        self.employee._valid_attendance_working_hours()

    def test_outside_working_hours(self):
        self.calendar.attendance_before = 0.0
        self.CalendarAttendance.search(
            [("calendar_id", "=", self.calendar.id)]
        ).unlink()
        day, _hour = self._current_day_and_hour()
        self.calendar_attendance_values.update(
            {
                "dayofweek": day,
                "hour_from": 0.0,
                "hour_to": 1.0,
            }
        )
        self.CalendarAttendance.create(self.calendar_attendance_values)
        with self.assertRaises(UserError):
            self.employee._valid_attendance_working_hours()

    def test_attendance_action_change_no_restriction(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "hr_attendance_resource_calendar.restriction_working_schdules", False
        )
        result = self.employee._attendance_action_change()
        self.assertIsInstance(result, type(self.HrAttendance))

    def test_attendance_action_change_restriction_true(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "hr_attendance_resource_calendar.restriction_working_schdules", True
        )
        with patch(
            "odoo.addons.hr_attendance.models.hr_employee.HrEmployee._attendance_action_change",
            return_value="OK",
        ) as mock_super:
            with patch.object(
                type(self.employee), "_valid_attendance_working_hours"
            ) as mock_valid:
                self.employee.attendance_state = "checked_in"
                self.employee._attendance_action_change()
                mock_valid.assert_called_once()
                mock_super.assert_called_once()
