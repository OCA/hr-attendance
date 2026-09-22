# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class HrAttendanceTimeCreditReportWizard(models.TransientModel):
    _name = "hr.attendance.time.credit.report.wizard"
    _description = "Time Credit Monthly Report Wizard"

    date_from = fields.Date(
        required=True,
        string="From",
        default=lambda self: date.today().replace(day=1),
        help="Start date of the reporting period (inclusive).",
    )
    date_to = fields.Date(
        required=True,
        string="To",
        default=lambda self: date.today().replace(day=1)
        + relativedelta(months=1, days=-1),
        help="End date of the reporting period (inclusive).",
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employees",
        help="Leave empty to include all employees visible to the current user.",
    )

    def action_print_report(self):
        """Return a report action for the QWeb PDF template."""
        self.ensure_one()
        report = self.env.ref(
            "hr_attendance_time_credit.action_report_time_credit_monthly"
        )
        action = report.report_action(self)
        # If report_action() returned a layout dialog (Odoo 17 behavior),
        # extract the actual report action from the context
        if (
            isinstance(action, dict)
            and action.get("type") == "ir.actions.act_window"
            and "report_action" in action.get("context", {})
        ):
            return action["context"]["report_action"]
        return action
