from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee.public"

    # hours_current_week = fields.Float(readonly=True)
    weekly_attendance_validation = fields.Boolean(readonly=True)
