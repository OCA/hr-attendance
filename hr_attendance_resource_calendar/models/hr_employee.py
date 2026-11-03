# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

import pytz

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import format_duration


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_attendance_schedule_lines(self, now_tz):
        """Working periods of the employee's calendar for the day of now_tz."""
        calendar = self.resource_calendar_id
        CalendarAttendance = self.env["resource.calendar.attendance"]
        domain = [
            ("calendar_id", "=", calendar.id),
            ("dayofweek", "=", str(now_tz.weekday())),
            ("day_period", "!=", "lunch"),
            ("display_type", "=", False),
        ]
        if calendar.two_weeks_calendar:
            week_type = CalendarAttendance.get_week_type(now_tz.date())
            domain.append(("week_type", "=", str(week_type)))
        return CalendarAttendance.search(domain, order="hour_from")

    def _valid_attendance_working_hours(self):
        calendar = self.resource_calendar_id
        tz = pytz.timezone(calendar.tz or "UTC")
        now_tz = datetime.now(tz)
        float_time = now_tz.hour + now_tz.minute / 60 + now_tz.second / 3600
        attendances = self._get_attendance_schedule_lines(now_tz)
        if not attendances:
            raise UserError(
                _(
                    "We're unable to register your attendance at this time. "
                    "Please check your assigned work schedule for today."
                )
            )
        margin = calendar.attendance_before
        if any(
            attendance.hour_from - margin <= float_time <= attendance.hour_to
            for attendance in attendances
        ):
            return
        schedules = "\n".join(
            f"\t{attendance.day_period.capitalize()}: "
            f"{format_duration(max(attendance.hour_from - margin, 0.0))} - "
            f"{format_duration(attendance.hour_to)}"
            for attendance in attendances
        )
        if any(
            attendance.hour_from - margin > float_time for attendance in attendances
        ):
            message = _(
                "It's not yet possible to register your attendance because "
                "your next shift hasn't started yet. You can do so from its "
                "start time. Thank you for your punctuality and understanding!"
                "\n\nSchedules:\n%(schedules)s"
            )
        else:
            message = _(
                "It's no longer possible to register your attendance because "
                "your workday has already ended."
                "\n\nSchedules:\n%(schedules)s"
            )
        raise UserError(message % {"schedules": schedules})

    def _attendance_action_change(self, geo_information=None):
        res = super()._attendance_action_change(geo_information)
        if (
            self.attendance_state == "checked_in"
            and self.company_id.restriction_working_schedules
        ):
            self._valid_attendance_working_hours()
        return res
