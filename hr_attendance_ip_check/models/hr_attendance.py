# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.constrains("check_in", "check_out", "employee_id")
    def _check_validity(self):
        for attendance in self:
            attendance.employee_id._attendance_ip_check()
        return super()._check_validity()
