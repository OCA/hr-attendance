# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    break_state = fields.Selection(
        related="employee_id.break_state",
        groups="hr_attendance.group_hr_attendance_kiosk,"
        "hr_attendance.group_hr_attendance",
    )
    break_hours_today = fields.Float(
        related="employee_id.break_hours_today",
        groups="hr_attendance.group_hr_attendance_kiosk,"
        "hr_attendance.group_hr_attendance",
    )
