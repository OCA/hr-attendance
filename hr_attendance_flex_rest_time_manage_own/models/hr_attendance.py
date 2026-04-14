# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.depends("overtime_status", "employee_id.attendance_manager_id")
    def _compute_is_rest_time_editable(self):
        super()._compute_is_rest_time_editable()
        user = self.env.user
        is_officer = user.has_group("hr_attendance.group_hr_attendance_officer")
        is_own_manager = user.has_group(
            "hr_attendance_manage_own.group_hr_attendance_own_manager"
        )
        if is_officer and is_own_manager:
            for rec in self.filtered(
                lambda r: r.employee_id.user_id == user
                and r.overtime_status != "approved"
            ):
                rec.is_rest_time_editable = True
        return
