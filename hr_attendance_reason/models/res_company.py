# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    show_reason_on_attendance_screen = fields.Boolean(
        string="Show reasons on attendance screen"
    )
    required_reason_on_attendance_screen = fields.Boolean(
        string="Required reason on attendance screen"
    )
