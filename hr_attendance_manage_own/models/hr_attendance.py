# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import AccessError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _is_attendance_manager_for_employees(self, employees):
        return self.env.user.has_group(
            "hr_attendance.group_hr_attendance_officer"
        ) and all(emp.attendance_manager_id.id == self.env.uid for emp in employees)

    def _is_own_manager_only(self):
        return self.env.user.has_group(
            "hr_attendance_manage_own.group_hr_attendance_own_manager"
        ) and not self.env.user.has_group("hr_attendance.group_hr_attendance_manager")

    def _is_processed(self):
        return (
            self.overtime_status != "to_approve"
            and self.employee_id.company_id.attendance_overtime_validation
            != "no_validation"
        )

    @api.constrains("overtime_status")
    def _check_overtime_status(self):
        if self.env.su or not self._is_own_manager_only():
            return
        for record in self:
            if record._is_attendance_manager_for_employees(record.employee_id):
                continue
            if record._is_processed():
                raise AccessError(
                    _("You are not allowed to change the overtime status.")
                )

    def _get_write_bypass_fields(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_attendance_manage_own.write_bypass_fields", "")
        )
        return {f.strip() for f in param.split(",") if f.strip()}

    def write(self, vals):
        if not self._is_own_manager_only():
            return super().write(vals)
        if self._is_attendance_manager_for_employees(self.employee_id):
            return super().write(vals)
        # Strip validated_overtime_hours so the compute determines its value.
        # The form client may include it in the payload when saving.
        vals = {k: v for k, v in vals.items() if k != "validated_overtime_hours"}
        bypass_fields = self._get_write_bypass_fields()
        if not set(vals.keys()) - bypass_fields:
            return super().write(vals)
        if self.filtered(lambda r: r._is_processed()):
            raise AccessError(
                _(
                    "You cannot modify attendance records that have already "
                    "been processed (approved or refused)."
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_check_processed(self):
        if self.env.su or not self._is_own_manager_only():
            return
        for record in self:
            if record._is_attendance_manager_for_employees(record.employee_id):
                continue
            if record._is_processed():
                raise AccessError(
                    _(
                        "You cannot delete attendance records that have already "
                        "been processed (approved or refused)."
                    )
                )
