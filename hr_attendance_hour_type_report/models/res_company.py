# Copyright 2021 Camptocamp SA
# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    hr_night_work_hour_start = fields.Float(
        "Beginning of night work time", default=22, help="expressed in company timezone"
    )
    hr_night_work_hour_end = fields.Float(
        "End of night work time", default=6, help="expressed in company timezone"
    )

    allow_weighting_nighttime_hours = fields.Boolean(
        string="Allow weighting of nighttime hours."
    )

    allow_weighting_overtime_hours = fields.Boolean(
        string="Allow weighting of overtime hours."
    )

    weighting_nighttime_hours = fields.Float(
        string="Weighting of nighttime hours.",
        default=1.00,
    )

    weighting_overtime_hours = fields.Float(
        string="Weighting of overtime hours.", default=1.00
    )
