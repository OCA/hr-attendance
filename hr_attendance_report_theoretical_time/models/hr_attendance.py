# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, time

from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    active = fields.Boolean(default=True)
    theoretical_hours = fields.Float(
        compute="_compute_theoretical_hours", store=True, compute_sudo=True
    )

    @api.depends("check_in", "employee_id")
    def _compute_theoretical_hours(self):
        obj = self.env["hr.attendance.theoretical.time.report"]
        for record in self:
            record.theoretical_hours = obj._theoretical_hours(
                record.employee_id, record.check_in
            )

    @api.model
    def _select(self):
        return super()._select() + """, hra.theoretical_hours"""

    @api.model
    def _from(self):
        res = super()._from()
        return res.replace("worked_hours", "worked_hours, theoretical_hours")

    def action_create_empty_attendance(
        self, limit_date_from=False, limit_date_to=False
    ):
        """Method for creating inactive attendance records with a
        duration of 0.
        The goal is to prevent the report from having to calculate data
        directly, so employee attendance records are created for past days
        when they should have clocked in."""
        today = fields.Date.today()
        yesterday = today - relativedelta(days=1)
        today_previous_year = today - relativedelta(months=1)
        limit_date_from = limit_date_from or today_previous_year
        day_to = datetime.combine(limit_date_to or yesterday, time.max)
        attendances = self.env["hr.attendance"]
        for employee in (
            self.env["hr.employee"]
            .sudo()
            .search([("resource_calendar_id", "!=", False)])
        ):
            date_from = (
                employee.theoretical_hours_start_date or employee.create_date.date()
            )
            date_from = max(date_from, limit_date_from)
            sql = """
            SELECT DISTINCT(check_in)::date
            FROM hr_attendance
            WHERE employee_id = %s
            AND check_out IS NOT NULL
            AND check_in::date >= %s
            AND check_in::date <= %s
            """
            params = [employee.id, date_from, yesterday]
            self.env.cr.execute(sql, params)
            attendance_dates = []
            for item in self.env.cr.fetchall():
                attendance_dates.append(item[0])
            day_from = datetime.combine(date_from, time.min)
            from_datetime = utc.localize(day_from).astimezone(
                timezone(employee.tz or "UTC")
            )
            to_datetime = utc.localize(day_to).astimezone(
                timezone(employee.tz or "UTC")
            )
            dates_to_create = {}
            expected_attendances = employee.resource_calendar_id._work_intervals_batch(
                from_datetime,
                to_datetime,
                resources=employee.resource_id,
                compute_leaves=False,
            )[employee.resource_id.id]
            for expected_attendance in expected_attendances:
                expected_attendance_date = expected_attendance[0].date()
                if (
                    expected_attendance_date not in attendance_dates
                    and expected_attendance_date not in dates_to_create
                ):
                    dates_to_create[expected_attendance_date] = expected_attendance
            attendance_vals = []
            for date_to_create in dates_to_create:
                attendance_vals.append(
                    {
                        "employee_id": employee.id,
                        "active": False,
                        "check_in": dates_to_create[date_to_create][0]
                        .astimezone(utc)
                        .replace(tzinfo=None),
                        "check_out": dates_to_create[date_to_create][0]
                        .astimezone(utc)
                        .replace(tzinfo=None)
                        + relativedelta(minutes=1),
                    }
                )
            attendances |= self.env["hr.attendance"].create(attendance_vals)
        return attendances
