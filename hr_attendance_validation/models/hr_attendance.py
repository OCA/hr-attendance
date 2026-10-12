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

    def _validated_attendances(self):
        return self.filtered(
            lambda attendance: attendance.validation_sheet_id.state == "validated"
        )

    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_validated(self):
        self._check_attendance_state_for_update(_("remove"))

    def _check_attendance_state_for_update(self, action_name):
        validated_attendances = self._validated_attendances()
        if validated_attendances:
            first_attendance = validated_attendances[:1]
            raise ValidationError(
                _(
                    "Can not %(action_name)s this attendance "
                    "(%(employee_name)s, %(checking_date)s) "
                    "which has been already reviewed and validated."
                )
                % dict(
                    employee_name=first_attendance.employee_id.name,
                    checking_date=first_attendance.check_in.date(),
                    action_name=action_name,
                )
            )

    def _is_validated_employee_week(self):
        self.ensure_one()
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

    @api.constrains("employee_id", "check_in")
    def _check_period_already_validated(self):
        for record in self:
            if record._is_validated_employee_week():
                raise ValidationError(
                    _(
                        "Can not edit attendance "
                        "(%(employee_name)s, %(checking_date)s) "
                        "which try to update a validated period."
                    )
                    % dict(
                        employee_name=record.employee_id.name,
                        checking_date=record.check_in.date(),
                    )
                )

    def write(self, *args, **kwargs):
        self._check_attendance_state_for_update(_("change"))
        res = super().write(*args, **kwargs)
        return res

    def _get_attendances_dates(self):
        # Overwriting odoo method to disable
        # HR attendance daily overtime computation
        daily_overtime_attendances = self.filtered(
            lambda att: not att.employee_id.weekly_attendance_validation
        )
        return super(HrAttendance, daily_overtime_attendances)._get_attendances_dates()
