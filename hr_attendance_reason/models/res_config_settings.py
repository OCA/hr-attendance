# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_reason_on_attendance_screen = fields.Boolean(
        related="company_id.show_reason_on_attendance_screen", readonly=False
    )
    required_reason_on_attendance_screen = fields.Boolean(
        related="company_id.required_reason_on_attendance_screen", readonly=False
    )
    reason_on_attendance_screen_default_sign_in = fields.Many2one(
        related="company_id.reason_on_attendance_screen_default_sign_in", readonly=False
    )
    reason_on_attendance_screen_default_sign_out = fields.Many2one(
        related="company_id.reason_on_attendance_screen_default_sign_out",
        readonly=False,
    )
