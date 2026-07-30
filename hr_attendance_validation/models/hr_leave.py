# Copyright 2021-2025 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import _, api, models
from odoo.exceptions import ValidationError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    @api.depends("holiday_status_id")
    def _compute_overtime_deductible(self):
        for leave in self:
            leave.overtime_deductible = leave.holiday_status_id.overtime_deductible

    def _check_overtime_deductible(self, leaves):
        # overwrite odoo code to allow negative extra hours
        for leave in leaves:
            if not leave.overtime_deductible:
                continue
            employee = leave.employee_id.sudo()
            duration = leave.number_of_hours_display
            # START overwrite
            if leave.holiday_status_id.requires_allocation == "yes":
                if (
                    not leave.holiday_status_id.allows_negative
                    and duration > employee.total_overtime
                ):
                    raise ValidationError(
                        _(
                            "The employee %(employee_name)s does not have enough "
                            "extra hours to request this leave."
                        )
                        % dict(employee_name=employee.name)
                    )
                if (
                    leave.holiday_status_id.allows_negative
                    and duration > employee.total_overtime
                    and employee.total_overtime + duration
                    > leave.holiday_status_id.max_allowed_negative
                ):
                    raise ValidationError(
                        _(
                            "You cannot request more than %(max_allowed_negative)s "
                            "extra hours requested %(duration)d "
                            "hours, currently %(overtime)d hours"
                        )
                        % dict(
                            max_allowed_negative=leave.holiday_status_id.max_allowed_negative,
                            duration=duration,
                            overtime=employee.total_overtime,
                        )
                    )
            # END overwrite
            if not leave.sudo().overtime_id:
                leave.sudo().overtime_id = (
                    self.env["hr.attendance.overtime"]
                    .sudo()
                    .create(
                        {
                            "employee_id": employee.id,
                            "date": leave.date_from,
                            "adjustment": True,
                            "duration": -1 * duration,
                        }
                    )
                )
