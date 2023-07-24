# Copyright 2020 Pavlov Media
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attendance_sheet_review_policy = fields.Selection(
        related="company_id.attendance_sheet_review_policy", readonly=False
    )
