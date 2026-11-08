# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    attendance_break_rounding_minutes = fields.Integer(
        string="Break Rounding (minutes)",
        default=0,
        help="Round each recorded break to the nearest number of minutes. "
        "Set to 0 to disable rounding and keep the exact duration.",
    )
