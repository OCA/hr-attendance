# Copyright 2018-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    include_in_theoretical = fields.Boolean(
        string="Include in theoretical hours",
        help="If you check this mark, leaves in this category won't reduce "
        "the number of theoretical hours in the attendance report.",
    )
    include_in_leave_theoretical = fields.Boolean(
        string="Include in leave hours",
        help="If you check this mark, leaves in this category won't reduce "
        "the number of leave hours in the attendance report.",
    )
