# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self, geo_information=None):
        attendance = super()._attendance_action_change(geo_information=geo_information)
        if self.env.context.get("attendance_reason_id"):
            attendance.attendance_reason_ids = [
                (4, self.env.context.get("attendance_reason_id"))
            ]
        return attendance
