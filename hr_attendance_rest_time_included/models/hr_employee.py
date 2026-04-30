# Copyright 2025 Tecnativa - Eduardo Ezerouali
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self, geo_information=None):
        self.ensure_one()
        RestTime = self.env["hr.attendance.rest_time"].sudo()
        # Close any open break for this employee
        open_break = RestTime.search(
            [("check_out", "=", False), ("employee_id", "=", self.id)], limit=1
        )
        if open_break:
            open_break.write({"check_out": fields.Datetime.now()})
            # Reopen the last attendance
            last_attendance = self.last_attendance_id
            if last_attendance and last_attendance.check_out:
                last_attendance.write({"check_out": False})
            return last_attendance
        res = super()._attendance_action_change(geo_information=geo_information)
        reason_id = self.env["hr.attendance.reason"].browse(
            self.env.context.get("attendance_reason_id")
        )
        if reason_id.rest_time_included:
            RestTime.sudo().create(
                {
                    "attendance_id": res.id,
                    "employee_id": self.id,
                    "check_in": res.check_out,
                    "check_out": False,
                }
            )
        return res
