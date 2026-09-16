# Copyright 2021 Camptocamp SA
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
