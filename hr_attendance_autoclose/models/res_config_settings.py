from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hr_attendance_autoclose_reason = fields.Many2one(
        related="company_id.hr_attendance_autoclose_reason",
        readonly=False,
    )
