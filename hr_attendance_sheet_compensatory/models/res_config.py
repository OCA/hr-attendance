# Copyright 2021 Pierre Verkest
# Copyright 2023 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hr_attendance_compensatory_leave_type_id = fields.Many2one(
        related="company_id.hr_attendance_compensatory_leave_type_id", readonly=False
    )
