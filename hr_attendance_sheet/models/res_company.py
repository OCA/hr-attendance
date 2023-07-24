# Copyright 2020 Pavlov Media
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_attendance_sheets = fields.Boolean("Use Attendance Sheets", default=False)

    attendance_sheet_review_policy = fields.Selection(
        string="Attendance Sheet Review Policy",
        selection=[
            ("hr", "HR Manager/Officer"),
            ("employee_manager", "Employee's Manager or Attendance Admin"),
            ("hr_or_manager", "HR or Employee's Manager or Attendance Admin"),
        ],
        default="hr",
        help="How Attendance Sheets review is performed.",
    )

    attendance_sheet_config_ids = fields.One2many(
        comodel_name="hr.attendance.sheet.config",
        inverse_name="company_id",
        string="Attendances Sheet Config",
    )
