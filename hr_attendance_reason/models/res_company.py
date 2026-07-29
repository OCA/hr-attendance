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

    reason_for_attendance_absence_detection = fields.Many2one(
        "hr.attendance.reason",
        string="Default attendance reason for absence detection",
        default=lambda self: self.env.ref(
            "hr_attendance_reason.attendance_reason_absence_detection",
            raise_if_not_found=False,
        ),
        help="The attendance reason set by the absence detection cron job on "
        "its generated attendances.",
    )
