# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    @api.constrains("date_from", "date_to")
    def _check_period(self):
        for wizard in self:
            if not wizard.date_from or not wizard.date_to:
                continue
            if wizard.date_from > wizard.date_to:
                raise ValidationError(
                    _("The start date cannot be later than the end date.")
                )
            # The report is monthly: a range crossing a month boundary would
            # silently print more than one month in the same table.
            if (wizard.date_from.year, wizard.date_from.month) != (
                wizard.date_to.year,
                wizard.date_to.month,
            ):
                raise ValidationError(_("The period must stay within a single month."))

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
