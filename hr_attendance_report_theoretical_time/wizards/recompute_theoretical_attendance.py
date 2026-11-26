# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, time, timedelta

from pytz import timezone, utc

from odoo import fields, models


class RecomputeTheoreticalAttendance(models.TransientModel):
    _name = "recompute.theoretical.attendance"
    _description = "Recompute Employees Attendances"

    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        required=True,
        string="Employees",
        help="Recompute these employees attendances",
        context={"active_test": False},
    )
    date_from = fields.Date(
        string="From", required=True, help="Recompute attendances from this date"
    )
    date_to = fields.Date(
        string="To", required=True, help="Recompute attendances up to this date"
    )

    def _action_recompute(self, attendances):
        """This method allows other modules to extend it to perform other actions
        and/or execute other methods compute from the corresponding attendances."""
        attendances._compute_theoretical_hours()
        attendances._compute_leave_hours()

    def action_recompute(self):
        self.ensure_one()
        for employee in self.employee_ids:
            # Create archived attendances for the days in the selected alendar date
            # range, when needed.
            # This method works with calendar dates, so timezone conversion is neither
            # required nor appropriate here.
            employee._action_create_empty_attendance(self.date_from, self.date_to)
            # Attendance check-in/check-out fields are datetimes stored in UTC.
            # Convert the selected calendar date range from the employee's timezone
            # into UTC datetime boundaries before searching for attendances.
            employee_tz = timezone(employee.tz or "UTC")
            datetime_from = (
                employee_tz.localize(datetime.combine(self.date_from, time.min))
                .astimezone(utc)
                .replace(tzinfo=None)
            )
            datetime_to = (
                employee_tz.localize(
                    datetime.combine(self.date_to + timedelta(days=1), time.min)
                )
                .astimezone(utc)
                .replace(tzinfo=None)
            )
            # Recompute all attendances that belong to the selected calendar date range.
            # The end boundary is the beginning of the following day, so the selected
            # end date is fully included.
            attendances = (
                self.env["hr.attendance"]
                .with_context(active_test=False)
                .search(
                    [
                        ("employee_id", "=", employee.id),
                        ("check_in", ">=", datetime_from),
                        ("check_out", "<=", datetime_to),
                    ]
                )
            )
            self._action_recompute(attendances)
        return {"type": "ir.actions.act_window_close"}
