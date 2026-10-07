# Copyright 2021 Camptocamp SA
# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hr_night_work_hour_start = fields.Float(
        related="company_id.hr_night_work_hour_start", readonly=False
    )
    hr_night_work_hour_end = fields.Float(
        related="company_id.hr_night_work_hour_end", readonly=False
    )

    allow_weighting_nighttime_hours = fields.Boolean(
        string="Allow weighting of nighttime hours.",
        related="company_id.allow_weighting_nighttime_hours",
        readonly=False,
    )

    allow_weighting_overtime_hours = fields.Boolean(
        string="Allow weighting of overtime hours.",
        related="company_id.allow_weighting_overtime_hours",
        readonly=False,
    )

    weighting_nighttime_hours = fields.Float(
        string="Weighting of nighttime hours.",
        related="company_id.weighting_nighttime_hours",
        readonly=False,
    )

    weighting_overtime_hours = fields.Float(
        string="Weighting of overtime hours.",
        related="company_id.weighting_overtime_hours",
        readonly=False,
    )
