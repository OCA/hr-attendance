# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attendance_break_rounding_minutes = fields.Integer(
        related="company_id.attendance_break_rounding_minutes",
        readonly=False,
    )
