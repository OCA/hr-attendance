# Copyright 2020 Pavlov Media
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_attendance_sheets = fields.Boolean(default=False)
    attendance_sheet_range = fields.Selection(
        selection=[
            ("MONTHLY", "Month"),
            ("BIWEEKLY", "Bi-Week"),
            ("WEEKLY", "Week"),
            ("DAILY", "Day"),
        ],
        default="WEEKLY",
        help="The range of your Attendance Sheet.",
    )

    @api.onchange("attendance_sheet_range")
    def onchange_attendance_sheet_range(self):
        if self.attendance_sheet_range == "MONTHLY":
            today = fields.Date.to_date(fields.Date.today())
            self._origin.write({"date_start": today.replace(day=1)})

    date_start = fields.Date(string="Date From", index=True, default=fields.Date.today)
    date_end = fields.Date(string="Date To", readonly=True, index=True)

    def _get_attendance_sheet_date_end(self, date_start, attendance_sheet_range):
        date_start = fields.Date.to_date(date_start)
        if date_start:
            if attendance_sheet_range == "WEEKLY":
                return date_start + relativedelta(days=6)
            elif attendance_sheet_range == "BIWEEKLY":
                return date_start + relativedelta(days=13)
            else:
                return date_start + relativedelta(months=1, day=1, days=-1)

    def set_date_end(self, company):
        company = self.browse(company)
        return company._get_attendance_sheet_date_end(
            company.date_start,
            company.attendance_sheet_range,
        )

    def write(self, vals):
        if "date_start" not in vals and "attendance_sheet_range" not in vals:
            return super().write(vals)
        for company in self:
            company_vals = vals.copy()
            company_vals["date_end"] = company._get_attendance_sheet_date_end(
                vals.get("date_start", company.date_start),
                vals.get("attendance_sheet_range", company.attendance_sheet_range),
            )
            super(ResCompany, company).write(company_vals)
        return True

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for company, vals in zip(res, vals_list, strict=True):
            if vals.get("date_start"):
                company.write({"date_end": company.set_date_end(company.id)})
        return res

    attendance_week_start = fields.Selection(
        selection=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Week Starting Day",
        default="0",
    )

    attendance_sheet_review_policy = fields.Selection(
        selection=[
            ("hr", "HR Manager/Officer"),
            ("employee_manager", "Employee's Manager or Attendance Admin"),
            ("hr_or_manager", "HR or Employee's Manager or Attendance Admin"),
        ],
        default="hr",
        help="How Attendance Sheets review is performed.",
    )

    auto_lunch = fields.Boolean(
        help="Applies a lunch period if duration is over the max time.",
    )

    auto_lunch_duration = fields.Float(
        string="Duration",
        help="The duration on an attendance that would trigger an auto lunch.",
    )

    auto_lunch_hours = fields.Float(
        string="Lunch Hours",
        help="Enter the lunch period that would be used for an auto lunch.",
    )
