# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_calendar_flexible = fields.Boolean(
        related="employee_id.resource_calendar_id.flexible_hours",
    )
    rest_time = fields.Float(
        help="Rest time in hours deducted from the total worked hours.",
        compute="_compute_rest_time",
        inverse="_inverse_rest_time",
        store=True,
        readonly=False,
        tracking=True,
        aggregator="sum",
    )
    is_rest_time_editable = fields.Boolean(compute="_compute_is_rest_time_editable")

    @api.depends("overtime_status", "employee_id.attendance_manager_id")
    def _compute_is_rest_time_editable(self):
        user = self.env.user
        is_manager = user.has_group("hr_attendance.group_hr_attendance_manager")
        is_officer = user.has_group("hr_attendance.group_hr_attendance_officer")
        for rec in self:
            if is_manager:
                rec.is_rest_time_editable = True
            elif is_officer and rec.employee_id.attendance_manager_id == self.env.user:
                rec.is_rest_time_editable = True
            else:
                rec.is_rest_time_editable = rec.overtime_status != "approved"

    @api.depends("employee_id", "check_in", "check_out")
    def _compute_rest_time(self):
        for rec in self:
            calendar = rec._get_employee_calendar()
            if (
                not calendar
                or not calendar.flexible_hours
                or not rec.check_in
                or not rec.check_out
            ):
                rec.rest_time = 0.0
                continue
            gross_hours = rec._get_worked_hours_in_range(rec.check_in, rec.check_out)
            rec.rest_time = calendar._get_rest_time(gross_hours)

    def _inverse_rest_time(self):
        self._update_overtime()

    @api.depends("check_in", "check_out", "rest_time", "employee_id")
    def _compute_worked_hours(self):
        res = super()._compute_worked_hours()
        for rec in self.filtered(lambda r: r.rest_time):
            rec.worked_hours -= rec.rest_time
        return res

    @api.constrains("rest_time")
    def _check_rest_time_positive(self):
        for rec in self:
            if rec.rest_time < 0:
                raise ValidationError(_("Rest time cannot be negative."))

    @api.constrains("rest_time", "check_in", "check_out")
    def _check_rest_time_not_exceed_gross_time(self):
        for rec in self:
            if not (rec.check_in and rec.check_out and rec.rest_time):
                continue
            gross_hours = rec._get_worked_hours_in_range(rec.check_in, rec.check_out)
            if rec.rest_time > gross_hours:
                raise ValidationError(
                    _(
                        "Rest time (%(rest).2f hours) cannot exceed the total"
                        " time between check in and check out"
                        " (%(gross).2f hours).",
                        rest=rec.rest_time,
                        gross=gross_hours,
                    )
                )

    def _get_pre_post_work_time(self, employee, working_times, attendance_date):
        """Subtract rest_time from work_duration so overtime is computed on net worked
        hours rather than gross (check-out - check-in) hours."""
        pre, work, post, planned = super()._get_pre_post_work_time(
            employee, working_times, attendance_date
        )
        total_rest = sum(self.mapped("rest_time"))
        return pre, work - total_rest, post, planned
