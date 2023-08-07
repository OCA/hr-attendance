# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from datetime import timedelta

from odoo import models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _update_overtime(self, employee_attendance_dates=None):
        """Compute overtime as $worked_hours - $(hours according to work calendar)"""
        # TODO: allow to configure this behavior per company
        for this in self:
            day_start_utc, date = self._get_day_start_and_day(
                this.employee_id, this.check_in
            )
            day_end_utc = day_start_utc + timedelta(days=1)
            # TODO: handle cases where an attendance spans multiple local days
            worked_hours = sum(
                self.search(
                    [
                        ("employee_id", "=", this.employee_id.id),
                        ("check_in", ">=", day_start_utc),
                        ("check_in", "<", day_end_utc),
                    ]
                ).mapped("worked_hours")
            )

            expected_hours = this.employee_id.with_context(
                # use hr_public_holidays if installed
                exclude_public_holidays=True,
            )._get_work_days_data_batch(day_start_utc, day_end_utc)[
                this.employee_id.id
            ][
                "hours"
            ]

            # TODO: support company thresholds
            overtime_hours = worked_hours - expected_hours

            overtime = (
                self.env["hr.attendance.overtime"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", this.employee_id.id),
                        ("date", "=", date),
                        ("adjustment", "=", False),
                    ]
                )
            )

            if not overtime:
                self.env["hr.attendance.overtime"].create(
                    {
                        "employee_id": this.employee_id.id,
                        "date": date,
                        "duration": overtime_hours,
                        "duration_real": overtime_hours,
                    }
                )
            else:
                overtime.write(
                    {
                        "duration": overtime_hours,
                        "duration_real": overtime_hours,
                    }
                )
