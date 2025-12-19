from odoo import api, fields, models


class HRAttendanceReport(models.Model):
    _inherit = "hr.attendance.report"

    rest_hours = fields.Float(string="Rest Time", readonly=True)

    @api.model
    def _select(self):
        return (
            super()._select()
            + """,
            hra.rest_hours
        """
        )

    @api.model
    def _from(self):
        return super()._from().replace("worked_hours", "worked_hours,\nrest_hours")
