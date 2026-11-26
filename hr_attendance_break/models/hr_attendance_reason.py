# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class HrAttendanceReason(models.Model):
    _inherit = "hr.attendance.reason"

    break_type_id = fields.Many2one(
        comodel_name="hr.attendance.break.type",
        help="Checking out with this reason starts a break of this type. "
        "The break ends when the employee checks in again.",
    )
