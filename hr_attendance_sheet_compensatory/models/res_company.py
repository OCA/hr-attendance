# Copyright 2021 Pierre Verkest
# Copyright 2023 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    hr_attendance_compensatory_leave_type_id = fields.Many2one(
        "hr.leave.type",
        "Overtime compensatory leave type",
        required=True,
        default=lambda self: self.env.ref("hr_holidays.holiday_status_comp"),
        help="Compensatory leave type used while validate weekly attendance sheet.",
    )
