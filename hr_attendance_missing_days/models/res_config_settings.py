# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attendance_missing_days_reason = fields.Many2one(
        related="company_id.attendance_missing_days_reason",
        readonly=False,
    )
