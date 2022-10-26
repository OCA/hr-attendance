from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attendance_maximum_hours_per_day = fields.Float(
        related="company_id.attendance_maximum_hours_per_day",
        readonly=False,
    )
    hr_attendance_autoclose_reason = fields.Many2one(
        related="company_id.hr_attendance_autoclose_reason",
        readonly=False,
    )
