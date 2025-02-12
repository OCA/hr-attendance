# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar
import datetime
from calendar import monthrange

from odoo import _, api, models
from odoo.exceptions import ValidationError


class HrReport(models.AbstractModel):
    _name = "report.hr_attendance_report.report_one_set"
    _description = "Attendance PDF Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        # Generate report values for PDF attendance report
        if not data or not data.get("form_data"):
            raise ValidationError(_("Missing report data."))

        form = data["form_data"]

        # Get and validate date parameters
        if not form.get("select_month") or not form.get("select_year"):
            raise ValidationError(_("Month and year are required."))

        try:
            month = int(form["select_month"])
            year = int(form["select_year"])
            start_date = datetime.date(year, month, 1)
            end_date = datetime.date(year, month, monthrange(year, month)[1])
        except (ValueError, TypeError) as e:
            raise ValidationError(
                _("Invalid month or year format: {}").format(str(e))
            ) from e

        # Get employees from form data
        employees = self._get_selected_employees(form)

        # Generate employee data
        employee_info_list = self._generate_employee_data(
            employees, start_date, end_date
        )

        return {
            "doc_ids": docids,
            "doc_model": "hr.employee",
            "form_data": form,
            "employees_data": employee_info_list,
            "month_name": calendar.month_name[month],
            "year": str(year),
            "start_date": start_date,
            "end_date": end_date,
            "total_employees": len(employees),
        }

    def _get_selected_employees(self, form):
        # Get selected employees from form data
        employee_ids = form.get("hr_employee_ids") or []
        department_ids = form.get("hr_department_ids") or []

        # Ensure IDs are lists
        if isinstance(employee_ids, int):
            employee_ids = [employee_ids]
        if isinstance(department_ids, int):
            department_ids = [department_ids]

        # Get employees by direct selection
        employees = self.env["hr.employee"].browse(employee_ids)

        # Add employees from selected departments
        if department_ids:
            dept_employees = self.env["hr.employee"].search(
                [("department_id", "in", department_ids)]
            )
            employees |= dept_employees  # Union without duplicates

        return employees

    def _generate_employee_data(self, employees, start_date, end_date):
        # Generate attendance data for each employee
        employee_info_list = []

        for emp in employees:
            # Get attendance records for the employee in the date range
            attendances = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", emp.id),
                    ("check_in", ">=", start_date),
                    ("check_in", "<=", end_date),
                ],
                order="check_in",
            )

            # Process attendance records
            attendance_data = []
            total_hours = 0
            dates_worked = set()  # Use set to count unique dates

            for att in attendances:
                worked_hours = round(att.worked_hours or 0, 2)
                total_hours += worked_hours

                # Add to unique dates if check_in exists
                if att.check_in:
                    dates_worked.add(att.check_in.date())

                attendance_data.append(
                    {
                        "check_in": att.check_in,
                        "check_out": att.check_out,
                        "worked_hours": worked_hours,
                        "date": att.check_in.date() if att.check_in else None,
                    }
                )

            # Compile employee information
            employee_info = {
                "emp_id": emp.id,
                "emp_name": emp.name or _("N/A"),
                "emp_code": emp.identification_id or emp.barcode or str(emp.id),
                "manager": emp.parent_id.name if emp.parent_id else _("N/A"),
                "department": emp.department_id.name if emp.department_id else _("N/A"),
                "job_title": emp.job_id.name if emp.job_id else _("N/A"),
                "attendances": attendance_data,
                "total_hours": round(total_hours, 2),
                "total_days": len(dates_worked),
                "avg_hours_per_day": round(total_hours / len(dates_worked), 2)
                if dates_worked
                else 0,
            }

            employee_info_list.append(employee_info)

        return employee_info_list
