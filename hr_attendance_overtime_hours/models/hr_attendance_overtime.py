# Copyright 2023 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from datetime import datetime, time

from odoo import api, fields, models


class HrAttendanceOvertime(models.Model):
    _inherit = "hr.attendance.overtime"

    planned_hours = fields.Float(compute="_compute_planned_hours", store=True)
    worked_hours = fields.Float(compute="_compute_worked_hours", store=True)

    @api.depends("date")
    def _compute_planned_hours(self):
        for overtime in self:
            # Get work hours from calendar
            planned_hours = (
                overtime.employee_id.resource_calendar_id.get_work_hours_count(
                    datetime.combine(overtime.date, time.min),
                    datetime.combine(overtime.date, time.max),
                    True,
                )
            )
            overtime.planned_hours = planned_hours

    @api.depends("duration")
    def _compute_worked_hours(self):
        for overtime in self:
            # Convert to UTC
            (
                datetime_check_in,
                datetime_check_out,
            ) = overtime.convert_check_in_check_out_to_utc(overtime.date)
            # Get sum of attendance entries
            attendance_ids = overtime.env["hr.attendance"].search(
                [
                    ("employee_id", "=", overtime.employee_id.id),
                    ("check_in", ">=", datetime_check_in),
                    ("check_out", "<=", datetime_check_out),
                ]
            )
            overtime.worked_hours = sum(attendance_ids.mapped("worked_hours"))

    def convert_check_in_check_out_to_utc(self, date_to_convert):
        tz = (
            self.employee_id.resource_calendar_id.tz
            or self.employee_id.tz
            or self.env.user.tz
        )
        datetime_tz_check_in = datetime.combine(date_to_convert, time.min)
        datetime_tz_check_out = datetime.combine(date_to_convert, time.max)
        datetime_check_in = self._convert_str_to_datetime(datetime_tz_check_in, tz)
        datetime_check_out = self._convert_str_to_datetime(datetime_tz_check_out, tz)
        return datetime_check_in, datetime_check_out

    def _convert_str_to_datetime(self, datetime_to_tz, tz):
        return fields.Datetime.from_string(
            self.env["ir.fields.converter"]
            .with_context(tz=tz)
            ._str_to_datetime(None, None, datetime_to_tz.replace(tzinfo=None))[0]
        )
