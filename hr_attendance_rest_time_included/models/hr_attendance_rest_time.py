# Copyright 2025 Tecnativa - Eduardo Ezerouali
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class HrAttendanceRestTime(models.Model):
    _inherit = "hr.attendance"
    _name = "hr.attendance.rest_time"
    _description = "Hr attendance break"

    attendance_id = fields.Many2one(
        comodel_name="hr.attendance",
        required=True,
        readonly=True,
        ondelete="cascade",
        index=True,
    )
