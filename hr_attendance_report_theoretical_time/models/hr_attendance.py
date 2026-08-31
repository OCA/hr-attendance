# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, time

from dateutil.relativedelta import relativedelta

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
        today = fields.Date.context_today(self)
        yesterday = today - relativedelta(days=1)
        today_previous_year = today - relativedelta(years=1)
        limit_date_from = limit_date_from or today_previous_year
        day_to = datetime.combine(limit_date_to or yesterday, time.max)
        attendances = self.env["hr.attendance"]
        for employee in (
            self.env["hr.employee"]
            .sudo()
            .search([("resource_calendar_id", "!=", False)])
        ):
            attendances += employee._action_create_empty_attendance(
                limit_date_from, day_to.date()
            )
        return attendances
