# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import datetime
from calendar import monthrange
from io import BytesIO

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
    include_approved_absences = fields.Boolean(default=True)
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
                _("Invalid month or year selection: %(error)s", error=str(e))
            ) from e

    def _get_selected_employees(self):
        """Get employees from direct selection and department selection."""
        if not self.env.user.has_group("hr_attendance.group_hr_attendance_manager"):
            employees = self.env["hr.employee"].search([("user_id", "=", self.env.uid)])
            if not employees:
                raise ValidationError(_("No employee is linked to the current user."))
            return employees

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
        self, workbook, employee, start_date, end_date, employee_data
    ):
        """Create an Excel sheet for a single employee's attendance data."""
        # Create sheet with truncated name (Excel limit is 31 chars)
        sheet_name = employee.name[:31] if len(employee.name) > 31 else employee.name
        sheet = workbook.add_worksheet(sheet_name)

        navy = "#17324D"
        teal = "#2A7F8E"
        slate = "#52667A"
        pale_blue = "#EEF4F6"
        border_color = "#D9E2E8"
        stripe_color = "#F8FAFB"
        absence_color = "#FFF5E6"
        absence_text = "#79501A"

        title_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 20,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": navy,
            }
        )
        subtitle_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 9,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": "#BFE2E7",
                "bg_color": navy,
            }
        )
        period_label_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 8,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": "#D8F0F3",
                "bg_color": teal,
                "border": 1,
                "border_color": teal,
            }
        )
        period_value_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 10,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": teal,
                "border": 1,
                "border_color": teal,
            }
        )
        info_label_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 8,
                "align": "left",
                "valign": "vcenter",
                "bold": True,
                "font_color": slate,
                "bg_color": "#F3F6F8",
                "border": 1,
                "border_color": border_color,
            }
        )
        info_value_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 10,
                "align": "left",
                "valign": "vcenter",
                "bold": True,
                "font_color": navy,
                "border": 1,
                "border_color": border_color,
            }
        )
        summary_label_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 8,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": slate,
                "bg_color": pale_blue,
                "top": 3,
                "top_color": teal,
            }
        )
        summary_value_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 16,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": navy,
                "bg_color": pale_blue,
            }
        )
        table_header_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 9,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": navy,
                "border": 1,
                "border_color": navy,
            }
        )

        body_common = {
            "font_name": "Arial",
            "font_size": 9,
            "align": "center",
            "valign": "vcenter",
            "font_color": "#243342",
            "border": 1,
            "border_color": border_color,
        }
        row_styles = {}
        for style_name, background, font_color in (
            ("body", "#FFFFFF", "#243342"),
            ("stripe", stripe_color, "#243342"),
            ("absence", absence_color, absence_text),
        ):
            row_style = {
                **body_common,
                "bg_color": background,
                "font_color": font_color,
            }
            row_styles[style_name] = {
                "date": workbook.add_format({**row_style, "num_format": "dd/mm/yyyy"}),
                "datetime": workbook.add_format(
                    {**row_style, "num_format": "dd/mm/yyyy hh:mm"}
                ),
                "text": workbook.add_format(row_style),
                "hours": workbook.add_format({**row_style, "bold": True}),
            }

        total_label_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 10,
                "align": "right",
                "valign": "vcenter",
                "bold": True,
                "font_color": navy,
                "bg_color": "#DCEBEF",
                "border": 1,
                "border_color": teal,
            }
        )
        total_value_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 11,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": teal,
                "border": 1,
                "border_color": teal,
            }
        )
        empty_style = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 9,
                "align": "center",
                "valign": "vcenter",
                "italic": True,
                "font_color": "#728394",
                "bg_color": stripe_color,
                "border": 1,
                "border_color": border_color,
            }
        )

        hours_unit = _("hrs")

        def format_hours(value):
            total_minutes = round(value * 60)
            return f"{total_minutes // 60:02d}:{total_minutes % 60:02d} {hours_unit}"

        sheet.hide_gridlines(2)
        sheet.set_tab_color(teal)
        sheet.set_column(0, 0, 14)
        sheet.set_column(1, 1, 24)
        sheet.set_column(2, 3, 21)
        sheet.set_column(4, 4, 17)
        sheet.set_row(0, 30)
        sheet.set_row(1, 18)
        sheet.set_row(2, 22)

        sheet.merge_range(0, 0, 0, 4, _("Employee Attendance Report"), title_style)
        sheet.merge_range(1, 0, 1, 4, employee_data["company_name"], subtitle_style)
        sheet.write(2, 0, _("From"), period_label_style)
        sheet.merge_range(
            2, 1, 2, 2, start_date.strftime("%d/%m/%Y"), period_value_style
        )
        sheet.write(2, 3, _("To"), period_label_style)
        sheet.write(2, 4, end_date.strftime("%d/%m/%Y"), period_value_style)

        employee_fields = (
            (_("Employee Name"), employee_data["emp_name"]),
            (_("Identification No"), employee_data["emp_identification"]),
            (_("Manager Name"), employee_data["manager"]),
            (_("Department"), employee_data["department"]),
            (_("Company"), employee_data["company_name"]),
            (_("CIF"), employee_data["company_vat"]),
        )
        for row, ((left_label, left_value), (right_label, right_value)) in enumerate(
            zip(employee_fields[::2], employee_fields[1::2], strict=False), start=4
        ):
            sheet.write(row, 0, left_label, info_label_style)
            sheet.merge_range(row, 1, row, 2, left_value, info_value_style)
            sheet.write(row, 3, right_label, info_label_style)
            sheet.write(row, 4, right_value, info_value_style)
            sheet.set_row(row, 21)

        summary_cards = (
            (
                0,
                1,
                _("Total Days Worked:"),
                employee_data["total_days"],
            ),
            (2, 3, _("Total Hours:"), format_hours(employee_data["total_hours"])),
            (
                4,
                4,
                _("Average Hours/Day:"),
                format_hours(employee_data["avg_hours_per_day"]),
            ),
        )
        for first_col, last_col, label, value in summary_cards:
            if first_col == last_col:
                sheet.write(8, first_col, label, summary_label_style)
                sheet.write(9, first_col, value, summary_value_style)
            else:
                sheet.merge_range(8, first_col, 8, last_col, label, summary_label_style)
                sheet.merge_range(9, first_col, 9, last_col, value, summary_value_style)
        sheet.set_row(8, 18)
        sheet.set_row(9, 28)

        table_header_row = 11
        sheet.write(table_header_row, 0, _("Date"), table_header_style)
        sheet.write(table_header_row, 1, _("Type"), table_header_style)
        sheet.write(table_header_row, 2, _("Check In"), table_header_style)
        sheet.write(table_header_row, 3, _("Check Out"), table_header_style)
        sheet.write(table_header_row, 4, _("Working Hours"), table_header_style)
        sheet.set_row(table_header_row, 23)

        # Write attendance and absence data
        row = table_header_row + 1
        for line in employee_data["lines"]:
            style_name = (
                "absence"
                if line["kind"] == "absence"
                else "stripe"
                if (row - table_header_row) % 2 == 0
                else "body"
            )
            styles = row_styles[style_name]
            report_date = datetime.datetime.combine(line["date"], datetime.time.min)
            sheet.write_datetime(row, 0, report_date, styles["date"])
            sheet.write(row, 1, line["type"], styles["text"])
            if line["kind"] == "attendance":
                sheet.write_datetime(row, 2, line["check_in_local"], styles["datetime"])
                if line["check_out_local"]:
                    sheet.write_datetime(
                        row, 3, line["check_out_local"], styles["datetime"]
                    )
                else:
                    sheet.write(row, 3, _("Still Working"), styles["text"])
                sheet.write(
                    row,
                    4,
                    format_hours(line["worked_hours"]),
                    styles["hours"],
                )
            else:
                sheet.write(row, 2, "-", styles["text"])
                sheet.write(row, 3, "-", styles["text"])
                sheet.write(row, 4, "-", styles["hours"])
            sheet.set_row(row, 20)
            row += 1

        if employee_data["lines"]:
            total_row = row + 1
            sheet.merge_range(
                total_row, 0, total_row, 3, _("Total Hours:"), total_label_style
            )
            sheet.write(
                total_row,
                4,
                format_hours(employee_data["total_hours"]),
                total_value_style,
            )
            sheet.set_row(total_row, 23)
            last_data_row = row - 1
        else:
            sheet.merge_range(
                row,
                0,
                row,
                4,
                _("No attendance or absence records found for this period"),
                empty_style,
            )
            sheet.set_row(row, 30)
            total_row = row
            last_data_row = table_header_row

        sheet.autofilter(table_header_row, 0, last_data_row, 4)
        sheet.freeze_panes(table_header_row + 1, 0)
        sheet.repeat_rows(table_header_row)
        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.fit_to_pages(1, 0)
        sheet.set_margins(0.3, 0.3, 0.5, 0.5)
        sheet.center_horizontally()
        sheet.set_footer("&C&P / &N")
        sheet.print_area(0, 0, total_row, 4)

        return sheet

    def generate_employee_excel_report(self):
        """Generate Excel attendance report with one sheet per employee."""
        if not self.select_month or not self.select_year:
            raise ValidationError(_("Please select a valid month and year."))

        start_date, end_date = self._get_month_date_range()
        employees = self._get_selected_employees()

        employee_data = self.env[
            "report.hr_attendance_report.report_one_set"
        ]._generate_employee_data(
            employees,
            start_date,
            end_date,
            include_absences=self.include_approved_absences,
        )
        employee_data_by_id = {item["emp_id"]: item for item in employee_data}

        # Create workbook
        stream = BytesIO()
        workbook = xlsxwriter.Workbook(stream, {"in_memory": True})

        # Generate filename with date range
        filename = "Attendance_Report_{}.xlsx".format(start_date.strftime("%Y_%m"))

        # Create sheets for each employee
        for employee in employees:
            try:
                self._create_excel_sheet_for_employee(
                    workbook,
                    employee,
                    start_date,
                    end_date,
                    employee_data_by_id[employee.id],
                )
            except Exception as e:
                raise ValidationError(
                    _(
                        "Error creating sheet for employee %(name)s: %(error)s",
                        name=employee.name,
                        error=str(e),
                    )
                ) from e

        # Save workbook to stream
        try:
            workbook.close()
            out = base64.encodebytes(stream.getvalue())
        except Exception as e:
            raise ValidationError(
                _("Error generating Excel file: %(error)s", error=str(e))
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
