# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class HrAttendanceReason(models.Model):
    _inherit = "hr.attendance.reason"

    action_type = fields.Selection(selection_add=[("break", "Break")])
    bypass_minimum_break = fields.Boolean(
        help="Check this to have breaks of this type always be counted, independent "
        "of minimum break settings"
    )
