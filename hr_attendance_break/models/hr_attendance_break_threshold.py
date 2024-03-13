# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class HrAttendanceBreakThreshold(models.Model):
    _name = "hr.attendance.break.threshold"
    _description = "Minimum break times"
    _rec_name = "company_id"
    _order = "min_hours desc"

    company_id = fields.Many2one("res.company", required=True, ondelete="cascade")
    min_hours = fields.Float(required=True)
    min_break = fields.Float(required=True)
