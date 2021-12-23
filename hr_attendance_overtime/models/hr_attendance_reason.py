# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class HrAttendanceReason(models.Model):
    _inherit = "hr.attendance.reason"

    description = fields.Char(
        string="Description",
        translate=True,
        help="Description displayed on kiosk while Check-in/Check-out."
        "Leave empty if you wish to display nothing.",
    )
