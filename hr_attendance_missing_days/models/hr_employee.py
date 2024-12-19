# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date, datetime, time, timedelta

import pytz

from odoo import models

_logger = logging.getLogger(__name__)


def ensure_tz(dt, tz=None):
    if not dt.tzinfo:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(tz) if tz else dt


class Employee(models.Model):
    _inherit = "hr.employee"

    def _prepare_missing_attendance_values(self, dt, reasons):
        self.ensure_one()
        return {
            "employee_id": self.id,
            "check_in": dt,
            "check_out": dt,
            "attendance_reason_ids": [(6, 0, reasons.ids)],
        }

    def _get_work_intervals_batch(self, dt_from, dt_to):
        self.ensure_one()
        return self.resource_calendar_id._work_intervals_batch(dt_from, dt_to)[False]

    def create_missing_attendances(self, date_from=None, date_to=None):
        for emp in self.search([]):
            emp._create_missing_attendances(date_from, date_to)

    def _create_missing_attendances(self, date_from=None, date_to=None):
        self.ensure_one()

        reason = self.env.company.sudo().attendance_missing_days_reason
        if not reason:
            return

        if not date_from:
            date_from = self.env.company.sudo().overtime_start_date

        if not date_to:
            date_to = date.today()

        # Ensure date_from and date_to are datetime objects, not just date objects
        if isinstance(
            date_from, date
        ):  # If date_from is a date object, convert it to datetime
            date_from = datetime.combine(date_from, time.min)
        if isinstance(
            date_to, date
        ):  # If date_to is a date object, convert it to datetime
            date_to = datetime.combine(date_to, time.max)

        tz = pytz.timezone(self.tz or "UTC")

        # Now they are datetime objects, we can safely localize them
        dt_from, dt_to = map(tz.localize, (date_from, date_to))

        # Ensure the time zone is set to UTC
        dt_from, dt_to = ensure_tz(dt_from, pytz.utc), ensure_tz(dt_to, pytz.utc)

        # Skip the active day
        if dt_to.replace(tzinfo=None) > datetime.now():
            dt_to -= timedelta(days=1)

        if dt_from > dt_to:
            return

        intervals = self._get_work_intervals_batch(dt_from, dt_to)
        work_dates = {}
        for start, _stop, _attendance in sorted(intervals):
            start_date = start.date()
            if start_date not in work_dates:
                work_dates[start_date] = ensure_tz(start, pytz.utc).replace(tzinfo=None)

        domain = [
            ("check_in", ">=", dt_from.replace(tzinfo=None)),
            ("check_in", "<=", dt_to.replace(tzinfo=None)),
        ]
        attendance_records = self.attendance_ids.filtered_domain(domain)

        attendances = set()
        for attendance_date in attendance_records.mapped("check_in"):
            if attendance_date:
                attendances.add(ensure_tz(attendance_date, tz).date())
        for attendance_date in attendance_records.mapped("check_out"):
            if attendance_date:  # Handle empty check_out field
                attendances.add(ensure_tz(attendance_date, tz).date())

        vals = []
        for missing in set(work_dates) - attendances:
            vals.append(
                self._prepare_missing_attendance_values(work_dates[missing], reason)
            )

        self.env["hr.attendance"].create(vals)
