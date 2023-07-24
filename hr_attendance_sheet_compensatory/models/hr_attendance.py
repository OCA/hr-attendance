# Copyright 2021 Pierre Verkest
# Copyright 2023 ACSONE SA/NV
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

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super().create(vals_list)
        for attendance in attendances:
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
        return attendances

    def unlink(self):
        for record in self:
            if record.attendance_sheet_id.state == "done":
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
        return super().unlink()

    def write(self, vals):
        allowed_fields = self.get_allowed_fields()
        is_allowed_fields = allowed_fields.issuperset(vals.keys())
        for record in self:
            if record.attendance_sheet_id.state == "done" and not is_allowed_fields:
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
        res = super().write(vals)
        for record in self:
            if record._is_validated_employee_week() and not is_allowed_fields:
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
            self.env["hr.attendance.sheet"]
            .with_user(SUPERUSER_ID)
            .search_count(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("state", "=", "done"),
                    ("start_date", "<=", self.check_in.date()),
                    ("end_date", ">=", self.check_in.date()),
                ]
            )
        )
        return validated_week > 0

    def get_allowed_fields(self):
        return {"auto_lunch"}
