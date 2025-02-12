# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
import datetime
from calendar import monthrange
from io import BytesIO

import xlwt

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


class CustomExcel(models.TransientModel):
    _name = "custom.excel.class"
    _rec_name = "datas_fname"
    _description = "Employee Attendance Excel Report Wizard"

    file_name = fields.Binary(string="Report File")
    datas_fname = fields.Char(string="Filename")


class EmployeeAttendanceReportWizard(models.TransientModel):
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
        default=str(datetime.date.today().month),
    )
    select_year = fields.Char(
        string="Year", required=True, default=str(datetime.date.today().year), size=4
    )

    @api.constrains("select_year")
    def _check_year_format(self):
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
        if self.select_all_employee:
            self.hr_employee_ids = self.env["hr.employee"].search([])
        if self.select_all_department:
            self.hr_department_ids = self.env["hr.department"].search([])

    @api.onchange("hr_employee_ids")
    def _onchange_hr_employee_ids(self):
        total_employees = self.env["hr.employee"].search_count([])
        selected_employees = len(self.hr_employee_ids)
        self.select_all_employee = selected_employees == total_employees

    @api.onchange("hr_department_ids")
    def _onchange_hr_department_ids(self):
        total_departments = self.env["hr.department"].search_count([])
        selected_departments = len(self.hr_department_ids)
        self.select_all_department = selected_departments == total_departments

    def _get_month_date_range(self):
        try:
            month = int(self.select_month)
            year = int(self.select_year)
            start = datetime.date(year, month, 1)
            end = datetime.date(year, month, monthrange(year, month)[1])
            return start, end
        except (ValueError, TypeError) as e:
            raise ValidationError(
                _("Invalid month or year selection: %(error)s").format(str(e))
            ) from e

    def _get_selected_employees(self):
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
        self, workbook, employee, start_date, end_date
    ):
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", employee.id),
                ("check_in", ">=", start_date),
                ("check_in", "<=", end_date),
            ],
            order="check_in",
        )

        # Create sheet with truncated name (Excel limit is 31 chars)
        sheet_name = employee.name[:31] if len(employee.name) > 31 else employee.name
        sheet = workbook.add_sheet(sheet_name)

        # Define styles
        date_format = xlwt.XFStyle()
        date_format.num_format_str = "yyyy/mm/dd hh:mm:ss"

        header_style = xlwt.easyxf(
            "align:horiz center;font:color black,bold True;"
            "borders:top_color black,bottom_color black,"
            "right_color black, left_color black,"
            "left thin, right thin,top thin, bottom thin;"
            "pattern:pattern solid, fore_color lavender"
        )

        center_style = xlwt.easyxf("align:horiz center")
        title_style = xlwt.easyxf(
            "align:horiz center;font:color black, height 300,bold True"
        )

        # Set column widths
        for col in range(3):
            sheet.col(col).width = 7000

        # Set row heights
        sheet.row(0).height = 250
        sheet.row(1).height = 250

        # Write title
        sheet.write_merge(0, 1, 0, 2, "Employee Attendance Report", title_style)

        # Write date range
        sheet.write(2, 0, "From", header_style)
        sheet.write(2, 1, "To", header_style)
        sheet.write(3, 0, start_date, date_format)
        sheet.write(3, 1, end_date, date_format)

        # Write employee info
        sheet.write(5, 0, "Employee Name", header_style)
        sheet.write(5, 1, "Manager Name", header_style)
        sheet.write(5, 2, "Department", header_style)

        sheet.write(6, 0, employee.name or "", center_style)
        sheet.write(6, 1, employee.parent_id.name or _("N/A"), center_style)
        sheet.write(6, 2, employee.department_id.name or _("N/A"), center_style)

        # Write attendance headers
        sheet.write(7, 0, "Check In", header_style)
        sheet.write(7, 1, "Check Out", header_style)
        sheet.write(7, 2, "Working Hours", header_style)

        # Write attendance data
        row = 8
        total_hours = 0
        for att in attendances:
            sheet.write(row, 0, att.check_in or "", date_format)
            sheet.write(row, 1, att.check_out or _("N/A"), date_format)

            worked_hours = att.worked_hours or 0
            total_hours += worked_hours

            # Convert decimal hours to HH:MM format
            hours = int(worked_hours)
            minutes = int((worked_hours - hours) * 60)
            time_display = _("{hours:02d}:{minutes:02d} hrs").format(
                hours=hours, minutes=minutes
            )

            sheet.write(row, 2, time_display, center_style)
            row += 1

        # Add total hours row
        if attendances:
            # Convert total to HH:MM format and show both
            total_hours_int = int(total_hours)
            total_minutes = int((total_hours - total_hours_int) * 60)
            total_display = f"{total_hours_int:02d}:{total_minutes:02d} hrs"

            sheet.write(row + 1, 1, "Total Hours:", header_style)
            sheet.write(row + 1, 2, total_display, header_style)

        return sheet

    def generate_employee_excel_report(self):
        if not self.select_month or not self.select_year:
            raise ValidationError(_("Please select a valid month and year."))

        start_date, end_date = self._get_month_date_range()
        employees = self._get_selected_employees()

        # Create workbook
        workbook = xlwt.Workbook(encoding="utf-8")

        # Generate filename with date range
        filename = f"Attendance_Report_{start_date.strftime('%Y_%m')}.xls"

        # Create sheets for each employee
        for employee in employees:
            try:
                self._create_excel_sheet_for_employee(
                    workbook, employee, start_date, end_date
                )
            except Exception as e:
                raise ValidationError(
                    _("Error creating sheet for employee %(name)s: %(error)s").format(
                        employee.name, str(e)
                    )
                ) from e

        # Save workbook to stream
        stream = BytesIO()
        try:
            workbook.save(stream)
            out = base64.encodebytes(stream.getvalue())
        except Exception as e:
            raise ValidationError(
                _("Error generating Excel file: %(error)s").format(str(e))
            ) from e
        finally:
            stream.close()

        # Create download record
        excel_id = self.env["custom.excel.class"].create(
            {
                "datas_fname": filename,
                "file_name": out,
            }
        )

        return {
            "res_id": excel_id.id,
            "name": "Employee Attendance Report",
            "view_mode": "form",
            "res_model": "custom.excel.class",
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
        }
