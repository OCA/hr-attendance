# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    hr_attendance_break_min_break = fields.Float("Minimal break length")
    hr_attendance_break_threshold_ids = fields.One2many(
        "hr.attendance.break.threshold",
        "company_id",
        string="Minimal break thresholds",
    )
