# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import api, fields, models


class HrAttendanceReport(models.Model):
    _inherit = "hr.attendance.report"

    break_hours = fields.Float(readonly=True)

    @api.model
    def _select(self):
        return super()._select().rstrip() + ", break_hours"

    @api.model
    def _from(self):
        return super()._from().replace("worked_hours", "worked_hours, break_hours")
