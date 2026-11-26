# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class HrAttendanceBreakType(models.Model):
    _name = "hr.attendance.break.type"
    _description = "Attendance Break Type"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company")
    paid = fields.Boolean(
        default=True,
        help="Paid breaks count as worked time. Unpaid breaks are deducted "
        "from the net worked hours of the attendance.",
    )
