# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

import pytz

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.resource.models.utils import float_to_time


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _valid_attendance_working_hours(self):
        tz = pytz.timezone(self.resource_calendar_id.tz or "UTC")
        now_tz = datetime.now(tz)
        day_week = str(now_tz.weekday())
        float_time = now_tz.hour + now_tz.minute / 60 + now_tz.second / 3600
        attendances = self.env["resource.calendar.attendance"].search(
            [
                ("calendar_id", "=", self.resource_calendar_id.id),
                ("dayofweek", "=", day_week),
                ("day_period", "!=", "lunch"),
            ]
        )
        if attendances:
            allow_attendance = False
            for attendance in attendances:
                attendance_before = (
                    attendance.hour_from - self.resource_calendar_id.attendance_before
                )
                if (
                    attendance.hour_from <= float_time <= attendance.hour_to
                    or attendance_before <= float_time <= attendance.hour_from
                ):
                    allow_attendance = True
                    break

            if not allow_attendance:

                def _get_interval_attendance(attendance):
                    hour_from = float_to_time(
                        attendance.hour_from
                        - self.resource_calendar_id.attendance_before
                    )
                    return (
                        f"\t{attendance.day_period.capitalize()}: "
                        f"{hour_from} - {float_to_time(attendance.hour_to)}"
                    )

                raise UserError(
                    _(
                        "It's not yet possible to register your attendance because "
                        "your assigned workday hasn't started yet. You can do so from "
                        "the start time of your shift. Thank you for your punctuality "
                        "and understanding!\n\n Schedules: \n%(shedules)s"
                    )
                    % {
                        "shedules": "\n".join(
                            attendances.mapped(_get_interval_attendance)
                        ),
                    }
                )
        else:
            raise UserError(
                _(
                    "We're unable to register your attendance at this time. "
                    "Please check your assigned work schedule for today."
                )
            )

    def _attendance_action_change(self, geo_information=None):
        res = super()._attendance_action_change(geo_information)
        apply_restriction = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_attendance_resource_calendar.restriction_working_schdules")
        )
        if self.attendance_state == "checked_in" and apply_restriction:
            self._valid_attendance_working_hours()
        return res
