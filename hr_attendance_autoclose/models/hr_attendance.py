# Copyright 2018 ForgeFlow, S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from collections import defaultdict

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _cron_auto_check_out(self):
        super()._cron_auto_check_out()

        def check_in_tz(attendance):
            return attendance.check_in.astimezone(
                pytz.timezone(attendance.employee_id.resource_calendar_id.tz or "UTC")
            )

        to_verify = self.env["hr.attendance"].search(
            [
                ("check_out", "=", False),
                ("employee_id.company_id.auto_check_out", "=", True),
                ("employee_id.resource_calendar_id.flexible_hours", "=", True),
            ]
        )

        if not to_verify:
            return

        previous_attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "in", to_verify.mapped("employee_id").ids),
                (
                    "check_in",
                    ">",
                    (fields.Datetime.now() - relativedelta(days=1)).replace(
                        hour=0, minute=0, second=0
                    ),
                ),
                ("check_out", "!=", False),
            ]
        )

        mapped_previous_duration = defaultdict(lambda: defaultdict(float))
        for previous in previous_attendances:
            tz_date = check_in_tz(previous).date()
            mapped_previous_duration[previous.employee_id][tz_date] += (
                previous.worked_hours
            )

        body = self.env._(
            "This attendance was automatically checked out because the employee "
            "exceeded the allowed time for their scheduled work hours."
        )

        for att in to_verify:
            calendar = att.employee_id.resource_calendar_id
            company = att.employee_id.company_id

            tz_check_in_date = check_in_tz(att).date()
            previous_hours = mapped_previous_duration[att.employee_id][tz_check_in_date]

            hours_per_day = calendar.hours_per_day
            tolerance = company.auto_check_out_tolerance
            allowed_hours = hours_per_day + tolerance

            open_hours = (fields.Datetime.now() - att.check_in).total_seconds() / 3600.0
            total_today_hours = previous_hours + open_hours

            if total_today_hours > allowed_hours:
                excess_hours = total_today_hours - allowed_hours
                new_check_out = max(
                    fields.Datetime.now() - relativedelta(hours=excess_hours),
                    att.check_in + relativedelta(seconds=1),
                )

                att.write(
                    {
                        "check_out": new_check_out,
                        "out_mode": "auto_check_out",
                    }
                )
                att.message_post(body=body)
