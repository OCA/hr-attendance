# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    attendance_missing_days_reason = fields.Many2one(
        "hr.attendance.reason",
        default=lambda self: self.env.ref(
            "hr_attendance_missing_days.attendance_reason_missing_days",
            raise_if_not_found=False,
        ),
    )
