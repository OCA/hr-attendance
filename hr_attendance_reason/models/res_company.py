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
    reason_on_attendance_screen_default_sign_in = fields.Many2one(
        "hr.attendance.reason",
        string="Default sign-in reason for attendance screen",
        domain=[
            ("action_type", "=", "sign_in"),
            ("show_on_attendance_screen", "=", True),
        ],
        check_company=True,
    )
    reason_on_attendance_screen_default_sign_out = fields.Many2one(
        "hr.attendance.reason",
        string="Default sign-out reason for attendance screen",
        domain=[
            ("action_type", "=", "sign_out"),
            ("show_on_attendance_screen", "=", True),
        ],
        check_company=True,
    )
