# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_reasons_on_attendance_screen = fields.Boolean(
        related="company_id.show_reasons_on_attendance_screen", readonly=False
    )
