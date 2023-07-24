# Copyright 2020 Pavlov Media
# Copyright 2023 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrAttendanceConfig(models.Model):
    _name = "hr.attendance.sheet.config"
    _description = "Configuration for Attendance Sheet Generation"

    period = fields.Selection(
        selection=[
            ("MONTHLY", "Month"),
            ("BIWEEKLY", "Bi-Week"),
            ("WEEKLY", "Week"),
            ("DAILY", "Day"),
        ],
        string="Attendance Sheet Range",
        default="WEEKLY",
        help="The range of your Attendance Sheet.",
        required=True,
    )

    start_date = fields.Date(
        string="Date From",
        required=True,
    )
    end_date = fields.Date(
        string="Date To",
    )

    auto_lunch = fields.Boolean(
        string="Auto Lunch",
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

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        (
            "check_date",
            "CHECK(start_date<=end_date)",
            _("Start_Date must be before to end_date"),
        ),
    ]

    @api.constrains("start_date", "end_date", "company_id")
    def check_dates(self):
        for config in self:
            existing_config = self.search(
                [
                    ("start_date", "<", config.end_date),
                    ("end_date", ">", config.start_date),
                    ("company_id", "=", config.company_id.id),
                    ("id", "!=", config.id),
                ],
                limit=1,
            )
            if existing_config:
                raise ValidationError(
                    _("There is already a Sheet Configuration for that period")
                )

    def compute_end_date(self, start_date):
        self.ensure_one()
        if self.period == "DAILY":
            return start_date + relativedelta(days=1)
        if self.period == "WEEKLY":
            return start_date + relativedelta(days=6)
        if self.period == "BIWEEKLY":
            return start_date + relativedelta(days=13)
        return start_date + relativedelta(months=1, day=1, days=-1)
