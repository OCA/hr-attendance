# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, time

import pytz

from odoo import models

_logger = logging.getLogger(__name__)


def ensure_tz(dt, tz=None):
    if not dt.tzinfo:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(tz) if tz else dt


class Employee(models.Model):
    _inherit = "hr.employee"

    def create_missing_attendances(self, date_from=None, date_to=None):
        for emp in self.search([]):
            emp._create_missing_attendances(date_from, date_to)

    def _create_missing_attendances(self, date_from=None, date_to=None):
        self.ensure_one()

        reason = self.env.company.sudo().attendance_missing_days_reason
        if not reason:
            return

        if not date_from:
            date_from = datetime.combine(
                self.env.company.sudo().overtime_start_date, time.min
            )

        if not date_to:
            date_to = datetime.now()

        date_from, date_to = map(ensure_tz, (date_from, date_to))

        intervals = self.resource_calendar_id._work_intervals_batch(date_from, date_to)
        work_dates = {}
        for start, _stop, _attendance in sorted(intervals[False]):
            start_date = start.date()
            if start_date not in work_dates:
                work_dates[start_date] = ensure_tz(start, pytz.utc).replace(tzinfo=None)

        domain = [
            ("check_in", ">=", date_from.replace(tzinfo=None)),
            ("check_in", "<=", date_to.replace(tzinfo=None)),
        ]
        tz = pytz.timezone(self.tz)
        attendances = {
            ensure_tz(attendance.check_in, tz).date()
            for attendance in self.attendance_ids.filtered_domain(domain)
        }

        vals = []
        for missing in set(work_dates) - attendances:
            vals.append(
                {
                    "employee_id": self.id,
                    "check_in": work_dates[missing],
                    "check_out": work_dates[missing],
                    "attendance_reason_ids": [(4, reason.id)],
                }
            )

        self.env["hr.attendance"].create(vals)
