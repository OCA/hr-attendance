# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


import logging
from datetime import date, datetime, time, timedelta

from pytz import timezone, utc

from odoo import models

_logger = logging.getLogger(__name__)


class HrAttendanceOvertime(models.Model):
    _inherit = "hr.attendance.overtime"

    def _compute_missing_overtime(self, companies=None, end_date=None):
        """Create overtime entries from company.overtime_start_date to end date or yesterday"""
        end_date = end_date or date.today() - timedelta(days=1)
        for company in (companies or self.env.company).filtered("overtime_start_date"):
            for employee in self.env["hr.employee"].search(
                [("company_id", "=", company.id)]
            ):
                self._compute_missing_overtime_employee(
                    employee, company.overtime_start_date, end_date
                )

    def _compute_missing_overtime_employee(self, employee, start_date, end_date):
        """Create overtime entries for employee from start_date to end_date"""
        employee_timezone = timezone(employee.tz)
        existing_overtime = set(
            self.env["hr.attendance.overtime"]
            .search(
                [
                    ("date", ">=", start_date),
                    ("date", "<=", end_date),
                    ("employee_id", "=", employee.id),
                    ("adjustment", "=", False),
                ]
            )
            .mapped("date")
        )
        overtime_date = start_date
        while overtime_date <= end_date:
            if overtime_date in existing_overtime:
                overtime_date += timedelta(days=1)
                continue
            _logger.info(
                "calculating overtime for #%d on %s", employee.id, overtime_date
            )
            employee_date = (
                employee_timezone.localize(datetime.combine(overtime_date, time()))
                .astimezone(utc)
                .replace(tzinfo=None)
            )

            self.env["hr.attendance"].new(
                {
                    "employee_id": employee.id,
                    "check_in": employee_date,
                    "check_out": employee_date,
                }
            )._update_overtime()
            overtime_date += timedelta(days=1)
