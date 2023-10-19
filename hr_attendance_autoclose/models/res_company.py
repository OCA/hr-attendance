# Copyright 2018 ForgeFlow, S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    attendance_maximum_hours_per_day = fields.Float(digits=(2, 2), default=11.0)
    hr_attendance_autoclose_reason = fields.Many2one(
        "hr.attendance.reason",
        default=lambda self: self.env.ref(
            "hr.attendance_reason.hr_attendance_reason_check_out",
            raise_if_not_found=False,
        ),
    )
