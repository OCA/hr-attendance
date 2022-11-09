from datetime import timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    hours_current_week = fields.Float(compute="_compute_hours_current_week")

    def _compute_hours(self, start_naive, end_naive):
        self.ensure_one()
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", self.id),
                "&",
                ("check_in", "<=", end_naive),
                ("check_out", ">=", start_naive),
                "|",
                ("is_overtime", "=", False),
                "&",
                ("is_overtime", "=", True),
                ("is_overtime_due", "=", True),
            ]
        )
        hours = 0
        for attendance in attendances:
            check_in = max(attendance.check_in, start_naive)
            check_out = min(attendance.check_out, end_naive)
            hours += (check_out - check_in).total_seconds() / 3600.0
        return hours

    def _compute_hours_current_week(self):
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
            tz = pytz.timezone(employee.tz or "UTC")
            now_tz = now_utc.astimezone(tz)
            # return last monday
            start_tz = (
                now_tz
                + timedelta(days=-now_tz.weekday())
                + relativedelta(hour=0, minute=0, second=0, microsecond=0)
            )
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            end_naive = now_tz.astimezone(pytz.utc).replace(tzinfo=None)
            hours = self._compute_hours(start_naive, end_naive)
            employee.hours_current_week = round(hours, 2)

    def _compute_hours_last_month(self):
        # Copied from hr_attendance module to overwrite hr.attendance search
        # and refactor with _compute_hours_current_week
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
            tz = pytz.timezone(employee.tz or "UTC")
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz + relativedelta(
                months=-1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            end_tz = now_tz + relativedelta(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end_naive = end_tz.astimezone(pytz.utc).replace(tzinfo=None)
            hours = self._compute_hours(start_naive, end_naive)
            employee.hours_last_month = round(hours, 2)
            employee.hours_last_month_display = "%g" % employee.hours_last_month

    def _compute_hours_today(self):
        # Copied from hr_attendance module to overwrite hr.attendance search
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
            # start of day in the employee's timezone might be the previous day in utc
            tz = pytz.timezone(employee.tz)
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz + relativedelta(
                hour=0, minute=0
            )  # day start in the employee's timezone
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)

            attendances = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("check_in", "<=", now),
                    "|",
                    ("check_out", ">=", start_naive),
                    ("check_out", "=", False),
                    "|",
                    ("is_overtime", "=", False),
                    "&",
                    ("is_overtime", "=", True),
                    ("is_overtime_due", "=", True),
                ]
            )

            worked_hours = 0
            for attendance in attendances:
                delta = (attendance.check_out or now) - max(
                    attendance.check_in, start_naive
                )
                worked_hours += delta.total_seconds() / 3600.0
            employee.hours_today = worked_hours
