# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    attendance_geolocation_required = fields.Boolean(
        string="Require Geolocation for Attendance",
        default=False,
    )
