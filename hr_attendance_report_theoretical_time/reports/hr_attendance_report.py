# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HRAttendanceReport(models.Model):
    _inherit = "hr.attendance.report"

    theoretical_hours = fields.Float(readonly=True)

    @api.model
    def _select(self):
        return super()._select() + """, hra.theoretical_hours"""

    @api.model
    def _from(self):
        res = super()._from()
        return res.replace("worked_hours", "worked_hours, theoretical_hours")
