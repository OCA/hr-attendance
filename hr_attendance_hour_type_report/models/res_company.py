from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    hr_night_work_hour_start = fields.Float(
        "Begining of night work time", default=22, help="expressed in company timezone"
    )
    hr_night_work_hour_end = fields.Float(
        "End of night work time", default=6, help="expressed in company timezone"
    )
