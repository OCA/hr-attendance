# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_overtime_due = fields.Boolean(
        string="Is overtime due",
        default=False,
        help="Whether the overtime is due or not. "
        "By default overtime is not due until a manager validates it.",
    )
    validation_sheet_id = fields.Many2one(
        "hr.attendance.validation.sheet",
        string="Validation sheet",
    )

    @api.model
    def create(self, *args, **kwargs):
        attendance = super().create(*args, **kwargs)
        if attendance._is_validated_employee_week():
            raise ValidationError(
                _(
                    "Cannot create new attendance for employee %s. "
                    "Attendance for the day of the check in %s "
                    "has already been reviewed and validated."
                )
                % (
                    attendance.employee_id.name,
                    attendance.check_in.date(),
                )
            )
        return attendance

    def unlink(self, *args, **kwargs):
        for record in self:
            if record.validation_sheet_id.state == "validated":
                raise ValidationError(
                    _(
                        "Can not remove this attendance (%s, %s) "
                        "which has been already reviewed and validated."
                    )
                    % (
                        record.employee_id.name,
                        record.check_in.date(),
                    )
                )
        return super().unlink(*args, **kwargs)

    def write(self, *args, **kwargs):
        for record in self:
            if record.validation_sheet_id.state == "validated":
                raise ValidationError(
                    _(
                        "Can not change this attendance (%s, %s) "
                        "which has been already reviewed and validated."
                    )
                    % (
                        record.employee_id.name,
                        record.check_in.date(),
                    )
                )
        res = super().write(*args, **kwargs)
        for record in self:
            if record._is_validated_employee_week():
                raise ValidationError(
                    _(
                        "Can not change this attendance (%s, %s) "
                        "which would be moved to a validated day."
                    )
                    % (
                        record.employee_id.name,
                        record.check_in.date(),
                    )
                )
        return res

    def _is_validated_employee_week(self):
        validated_week = (
            self.env["hr.attendance.validation.sheet"]
            .with_user(SUPERUSER_ID)
            .search_count(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("state", "=", "validated"),
                    ("date_from", "<=", self.check_in.date()),
                    ("date_to", ">=", self.check_in.date()),
                ]
            )
        )
        return validated_week > 0
