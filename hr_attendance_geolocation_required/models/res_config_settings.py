# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attendance_geolocation_required = fields.Boolean(
        related="company_id.attendance_geolocation_required",
        readonly=False,
    )
