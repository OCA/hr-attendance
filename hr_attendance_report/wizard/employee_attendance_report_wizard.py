# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import datetime
from calendar import monthrange
from io import BytesIO

import pytz
import xlsxwriter

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MONTH_SELECTION = [
    ("1", "January"),
    ("2", "February"),
    ("3", "March"),
    ("4", "April"),
    ("5", "May"),
    ("6", "June"),
    ("7", "July"),
    ("8", "August"),
    ("9", "September"),
    ("10", "October"),
    ("11", "November"),
    ("12", "December"),
]


class HrAttendanceReportDownload(models.TransientModel):
    """Transient model for downloading Excel attendance reports."""

    _name = "hr.attendance.report.download"
    _rec_name = "datas_fname"
    _description = "Employee Attendance Excel Report Download"

    file_name = fields.Binary(string="Report File")
    datas_fname = fields.Char(string="Filename")


class EmployeeAttendanceReportWizard(models.TransientModel):
    """Wizard for generating employee attendance reports in PDF and Excel."""

    _name = "employee.attendance.report.wizard"
    _description = "Employee Attendance Report Wizard"

    hr_employee_ids = fields.Many2many("hr.employee", string="Employees Selection")
    hr_department_ids = fields.Many2many(
        "hr.department", string="Departments Selection"
    )
    select_all_employee = fields.Boolean(default=False, string="Select All Employees")
    select_all_department = fields.Boolean(
        default=False, string="Select All Departments"
    )
    select_month = fields.Selection(
        MONTH_SELECTION,
        string="Month",
        required=True,
        default=lambda self: str(fields.Date.today().month),
    )
    select_year = fields.Char(
        string="Year",
        required=True,
        default=lambda self: str(fields.Date.today().year),
        size=4,
    )

    @api.model
    def default_get(self, fields_list):
        """Set default employee for non-managers."""
        res = super().default_get(fields_list)
        # If not attendance manager, set current user's employee by default
        if not self.env.user.has_group("hr_attendance.group_hr_attendance_manager"):
            employee = self.env["hr.employee"].search(
                [("user_id", "=", self.env.uid)], limit=1
            )
            if employee:
                res["hr_employee_ids"] = [(6, 0, [employee.id])]
        return res

    @api.constrains("select_year")
    def _check_year_format(self):
        """Validate year is a valid 4-digit number."""
        for record in self:
            if record.select_year:
                try:
                    int(record.select_year)
                except ValueError:
                    raise ValidationError(
                        _("Please enter a valid 4-digit year")
                    ) from None

    @api.onchange("select_all_employee", "select_all_department")
    def _onchange_select_all(self):
        """Select all employees or departments when checkbox is checked."""
        if self.select_all_employee:
            self.hr_employee_ids = self.env["hr.employee"].search([])
        if self.select_all_department:
            self.hr_department_ids = self.env["hr.department"].search([])

    @api.onchange("hr_employee_ids")
    def _onchange_hr_employee_ids(self):
        """Update select_all_employee based on selection."""
        total_employees = self.env["hr.employee"].search_count([])
        selected_employees = len(self.hr_employee_ids)
        self.select_all_employee = selected_employees == total_employees

    @api.onchange("hr_department_ids")
    def _onchange_hr_department_ids(self):
        """Update select_all_department based on selection."""
        total_departments = self.env["hr.department"].search_count([])
        selected_departments = len(self.hr_department_ids)
        self.select_all_department = selected_departments == total_departments

    def _get_month_date_range(self):
        """Calculate start and end dates for the selected month."""
        try:
            month = int(self.select_month)
            year = int(self.select_year)
            start = datetime.date(year, month, 1)
            end = datetime.date(year, month, monthrange(year, month)[1])
            return start, end
        except (ValueError, TypeError) as e:
            raise ValidationError(
                _("Invalid month or year selection: %(error)s") % {"error": str(e)}
            ) from e

    def _get_selected_employees(self):
        """Get employees from direct selection and department selection."""
        employees = self.hr_employee_ids

        if self.hr_department_ids:
            dept_employees = self.env["hr.employee"].search(
                [("department_id", "in", self.hr_department_ids.ids)]
            )
            employees |= dept_employees  # Union without duplicates

        if not employees:
            raise ValidationError(
                _("Please select at least one employee or department.")
            )

        return employees

    def generate_employee_pdf_report(self):
        """Generate PDF attendance report."""
        if not self.select_month or not self.select_year:
            raise ValidationError(_("Please select both a month and a year."))

        start_date, end_date = self._get_month_date_range()
        employees = self._get_selected_employees()

        data = {
            "form_data": self.read()[0],
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            },
            "employee_count": len(employees),
        }
        return self.env.ref(
            "hr_attendance_report.action_report_attendance_report_wizard"
        ).report_action(self, data=data)

    def _create_excel_sheet_for_employee(
        self, workbook, employee, start_date, end_date, attendances
    ):
        """Create an Excel sheet for a single employee's attendance data."""
        # Create sheet with truncated name (Excel limit is 31 chars)
        sheet_name = employee.name[:31] if len(employee.name) > 31 else employee.name
        sheet = workbook.add_worksheet(sheet_name)

        # Define styles
        date_format = workbook.add_format({"num_format": "yyyy/mm/dd hh:mm:ss"})

        header_style = workbook.add_format(
            {
                "align": "center",
                "bold": True,
                "font_color": "black",
                "border": 1,
                "bg_color": "#CC99FF",
            }
        )

        center_style = workbook.add_format({"align": "center"})
        title_style = workbook.add_format(
            {
                "align": "center",
                "bold": True,
                "font_color": "black",
                "font_size": 15,
            }
        )

        # Set column widths
        sheet.set_column(0, 3, 27)

        # Set row heights
        sheet.set_row(0, 12.5)
        sheet.set_row(1, 12.5)

        # Write title
        sheet.merge_range(0, 0, 1, 3, _("Employee Attendance Report"), title_style)

        # Write date range
        sheet.write(2, 0, _("From"), header_style)
        sheet.write(2, 1, _("To"), header_style)
        sheet.write(3, 0, start_date, date_format)
        sheet.write(3, 1, end_date, date_format)

        # Write employee info headers
        sheet.write(5, 0, _("Employee Name"), header_style)
        sheet.write(5, 1, _("Identification No"), header_style)
        sheet.write(5, 2, _("Manager Name"), header_style)
        sheet.write(5, 3, _("Department"), header_style)

        # Use sudo() consistently for restricted fields
        emp_sudo = employee.sudo()
        sheet.write(6, 0, employee.name or "", center_style)
        sheet.write(6, 1, emp_sudo.identification_id or "N/A", center_style)
        sheet.write(
            6,
            2,
            employee.parent_id.name if employee.parent_id else "N/A",
            center_style,
        )
        sheet.write(
            6,
            3,
            employee.department_id.name if employee.department_id else "N/A",
            center_style,
        )

        # Write company info
        sheet.write(7, 0, _("Company"), header_style)
        sheet.write(7, 1, _("CIF"), header_style)
        sheet.write(8, 0, employee.company_id.name or "N/A", center_style)
        sheet.write(8, 1, employee.company_id.vat or "N/A", center_style)

        # Write attendance headers
        sheet.write(10, 0, _("Check In"), header_style)
        sheet.write(10, 1, _("Check Out"), header_style)
        sheet.write(10, 2, _("Working Hours"), header_style)

        # Write attendance data
        row = 11
        total_hours = 0
        user_tz = pytz.timezone(self.env.user.tz or "UTC")
        for att in attendances:
            check_in = (
                pytz.utc.localize(att.check_in).astimezone(user_tz).replace(tzinfo=None)
                if att.check_in
                else ""
            )
            check_out = (
                pytz.utc.localize(att.check_out)
                .astimezone(user_tz)
                .replace(tzinfo=None)
                if att.check_out
                else "N/A"
            )
            sheet.write(row, 0, check_in or "", date_format)
            sheet.write(row, 1, check_out or "N/A", date_format)

            worked_hours = att.worked_hours or 0
            total_hours += worked_hours

            # Convert decimal hours to HH:MM format
            hours = int(worked_hours)
            minutes = int((worked_hours - hours) * 60)
            time_display = f"{hours:02d}:{minutes:02d} hrs"

            sheet.write(row, 2, time_display, center_style)
            row += 1

        # Add total hours row
        if attendances:
            # Convert total to HH:MM format
            total_hours_int = int(total_hours)
            total_minutes = int((total_hours - total_hours_int) * 60)
            total_display = f"{total_hours_int:02d}:{total_minutes:02d} hrs"

            sheet.write(row + 1, 1, _("Total Hours:"), header_style)
            sheet.write(row + 1, 2, total_display, header_style)

        return sheet

    def generate_employee_excel_report(self):
        """Generate Excel attendance report with one sheet per employee."""
        if not self.select_month or not self.select_year:
            raise ValidationError(_("Please select a valid month and year."))

        start_date, end_date = self._get_month_date_range()
        employees = self._get_selected_employees()

        # Single search for all employees' attendances (performance optimization)
        all_attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "in", employees.ids),
                ("check_in", ">=", start_date),
                ("check_in", "<=", end_date),
            ],
            order="employee_id, check_in",
        )

        # Group attendances by employee_id
        attendances_by_employee = {}
        for att in all_attendances:
            attendances_by_employee.setdefault(att.employee_id.id, []).append(att)

        # Create workbook
        stream = BytesIO()
        workbook = xlsxwriter.Workbook(stream, {"in_memory": True})

        # Generate filename with date range
        filename = "Attendance_Report_{}.xlsx".format(start_date.strftime("%Y_%m"))

        # Create sheets for each employee
        for employee in employees:
            try:
                emp_attendances = attendances_by_employee.get(employee.id, [])
                self._create_excel_sheet_for_employee(
                    workbook, employee, start_date, end_date, emp_attendances
                )
            except Exception as e:
                raise ValidationError(
                    _("Error creating sheet for employee %(name)s: %(error)s")
                    % {"name": employee.name, "error": str(e)}
                ) from e

        # Save workbook to stream
        try:
            workbook.close()
            out = base64.encodebytes(stream.getvalue())
        except Exception as e:
            raise ValidationError(
                _("Error generating Excel file: %(error)s") % {"error": str(e)}
            ) from e
        finally:
            stream.close()

        # Create download record
        excel_id = self.env["hr.attendance.report.download"].create(
            {
                "datas_fname": filename,
                "file_name": out,
            }
        )

        return {
            "res_id": excel_id.id,
            "name": _("Employee Attendance Report"),
            "view_mode": "form",
            "res_model": "hr.attendance.report.download",
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
        }
