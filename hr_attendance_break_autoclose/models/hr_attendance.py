# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import api, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.depends("break_hours")
    def _compute_open_worked_hours(self):
        result = super()._compute_open_worked_hours()
        for this in self:
            this.open_worked_hours -= this.break_hours
        return result
