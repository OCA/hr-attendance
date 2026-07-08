# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime as dt
import logging

import pytz

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    worked_hours_nighttime = fields.Float(
        string="Night hours", compute="_compute_worked_hours", store=True
    )
    worked_hours_daytime = fields.Float(
        string="Day hours",
        compute="_compute_worked_hours",
        store=True,
        readonly=True,
    )
    date = fields.Date(
        help="date of the attendance, from the payroll point of view",
        compute="_compute_date",
        store=True,
    )
    date_type = fields.Selection(
        [("normal", "Weekday"), ("sunday", "Sunday"), ("holiday", "Public Holiday")],
        compute="_compute_date_type",
        store=True,
    )

    @api.depends("date")
    def _compute_date_type(self):
        for rec in self:
            if rec.date.weekday() == 6:
                rec.date_type = "sunday"
            elif self.env["calendar.public.holiday"].get_holidays_list(
                start_dt=rec.date,
                end_dt=rec.date,
                partner_id=rec.employee_id.address_id.id,
            ):
                rec.date_type = "holiday"
            else:
                rec.date_type = "normal"

    @api.depends("check_in")
    def _compute_date(self):
        UTC = pytz.timezone("utc")
        for rec in self:
            tz = rec.employee_id.tz
            check_in = rec.check_in
            if not check_in.tzinfo:
                check_in = UTC.localize(check_in)
            check_in_tz = check_in.astimezone(pytz.timezone(tz))
            rec.date = check_in_tz.date()

    @api.depends("check_in", "check_out", "worked_hours")
    def _compute_worked_hours(self):
        res = super()._compute_worked_hours()
        UTC = pytz.timezone("utc")
        for record in self:
            record.worked_hours_nighttime = 0
            record.worked_hours_daytime = 0
            if not record.check_out:
                continue
            if record.worked_hours > 24:
                raise exceptions.UserError(
                    _("More than 24h of work in 1 shift is forbidden")
                )
            night_start = record.employee_id.company_id.hr_night_work_hour_start
            hour_night_start = int(night_start)
            minute_night_start = int(60 * (night_start - hour_night_start))
            night_end = record.employee_id.company_id.hr_night_work_hour_end
            hour_night_end = int(night_end)
            minute_night_end = int(60 * (night_end - hour_night_end))
            tz = pytz.timezone(record.employee_id.tz)
            check_in = UTC.localize(record.check_in)
            check_out = UTC.localize(record.check_out)
            curr_day_night_start = tz.localize(
                dt.datetime.combine(
                    record.date,
                    dt.time(hour=hour_night_start, minute=minute_night_start),
                )
            ).astimezone(UTC)
            curr_day_night_end = tz.localize(
                dt.datetime.combine(
                    record.date, dt.time(hour=hour_night_end, minute=minute_night_end)
                )
            ).astimezone(UTC)
            next_day_night_start = tz.localize(
                dt.datetime.combine(
                    record.date + dt.timedelta(days=1),
                    dt.time(hour=hour_night_start, minute=minute_night_start),
                )
            ).astimezone(UTC)
            next_day_night_end = tz.localize(
                dt.datetime.combine(
                    record.date + dt.timedelta(days=1),
                    dt.time(hour=hour_night_end, minute=minute_night_end),
                )
            ).astimezone(UTC)
            record.worked_hours_nighttime += (
                min(check_out, curr_day_night_end) - min(curr_day_night_end, check_in)
            ).total_seconds() / 3600.0
            if check_out > curr_day_night_start:
                record.worked_hours_nighttime += (
                    min(check_out, next_day_night_end)
                    - max(check_in, curr_day_night_start)
                ).total_seconds() / 3600.0
            record.worked_hours_nighttime += (
                max(check_out, next_day_night_start) - next_day_night_start
            ).total_seconds() / 3600.0
            if check_out > next_day_night_start:
                _logger.warning(
                    "very long_shift for employee %s", record.employee_id.id
                )
            record.worked_hours_daytime = (
                record.worked_hours - record.worked_hours_nighttime
            )
        return res
