from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrAttendanceReportWizard(models.TransientModel):
    _name = "hr.attendance.report.wizard"
    _description = "Hr Attendance Report Wizard"

    report_type = fields.Selection(
        selection=[
            ("individual", "By employee"),
            ("department", "By department"),
        ],
        string="Type of report",
        required=True,
        default="individual",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        required=True,
        check_company=True,
    )

    department_ids = fields.Many2many(
        comodel_name="hr.department",
        required=True,
        check_company=True,
    )

    date_from = fields.Date(
        string="Start date",
        required=True,
    )

    date_to = fields.Date(
        string="End date",
        required=True,
    )

    detailed = fields.Boolean(
        string="Detailed report",
        default=False,
        help="if enabled, the report will show each attendance record. "
        "Otherwise, it will show a summary per day.",
    )

    include_open_attendances = fields.Boolean(
        string="Include open attendances",
        default=False,
        help="Includes records without check_out. Duration will not be calculated for them.",
    )
    time_format = fields.Selection(
        selection=[
            ("hhmm", "hh:mm"),
            ("decimal", "Decimal"),
        ],
        string="Hours format",
        required=True,
        default="hhmm",
    )

    @api.constrains(
        "date_from", "date_to", "report_type", "employee_ids", "department_ids"
    )
    def _validate_attendance_report_fields(self):
        for record in self:
            if record.date_from > date.today() or record.date_to > date.today():
                raise ValidationError(_("Please select a valid date range."))

            if (
                record.date_from
                and record.date_to
                and record.date_from > record.date_to
            ):
                raise ValidationError(_("Start date cannot be after end date."))
            if record.report_type == "individual" and not record.employee_ids:
                raise ValidationError(
                    _("You must select an employee for the individual report.")
                )
            if record.report_type == "department" and not record.department_ids:
                raise ValidationError(
                    _("You must select a department for the department report.")
                )

    def action_print_report(self):
        self.ensure_one()
        data = {
            "report_type": self.report_type,
            "employee_ids": self.employee_ids.ids,
            "department_ids": self.department_ids.ids,
            "company_id": self.company_id.id or self.env.company.id,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "detailed": self.detailed,
            "include_open_attendances": self.include_open_attendances,
            "time_format": self.time_format,
        }
        return (
            self.env.ref("hr_attendance_report_pdf.action_report_attendance")
            .with_context(tz=self.env.user.tz)
            .report_action(self, data)
        )
