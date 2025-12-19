# Copyright 2025 Tecnativa - Eduardo Ezerouali
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class HrAttendanceReason(models.Model):
    _inherit = "hr.attendance.reason"

    rest_time_included = fields.Boolean()
