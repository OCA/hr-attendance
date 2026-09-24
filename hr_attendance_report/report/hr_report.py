# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
from calendar import monthrange
from collections import defaultdict

import pytz

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date


class HrReport(models.AbstractModel):
    """Abstract model for generating attendance PDF reports."""

    _name = "report.hr_attendance_report.report_one_set"
    _description = "Attendance PDF Report"

    def _has_hr_holidays(self):
        return "hr.leave" in self.env.registry

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate report values for PDF attendance report."""
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
                _("Invalid month or year format: %(error)s", error=str(e))
            ) from e

        # Get employees from form data
        employees = self._get_selected_employees(form)

        # Generate employee data
        employee_info_list = self._generate_employee_data(
            employees,
            start_date,
            end_date,
            include_absences=form.get("include_approved_absences", True),
        )

        return {
            "doc_ids": docids,
            "doc_model": "hr.employee",
            "form_data": form,
            "employees_data": employee_info_list,
            "month_name": format_date(self.env, start_date, date_format="MMMM"),
            "year": str(year),
            "start_date": start_date,
            "end_date": end_date,
            "total_employees": len(employees),
            "total_days_label": _("Total Days Worked:"),
            "total_hours_label": _("Total Hours:"),
            "average_hours_label": _("Average Hours/Day:"),
        }

    def _get_selected_employees(self, form):
        """Get selected employees from form data."""
        if not self.env.user.has_group("hr_attendance.group_hr_attendance_manager"):
            employees = self.env["hr.employee"].search([("user_id", "=", self.env.uid)])
            if not employees:
                raise ValidationError(_("No employee is linked to the current user."))
            return employees

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

    def _employee_month_bounds(self, employee, start_date, end_date):
        try:
            timezone = pytz.timezone(employee._get_tz())
        except pytz.UnknownTimeZoneError:
            timezone = pytz.utc
        local_start = timezone.localize(
            datetime.datetime.combine(start_date, datetime.time.min)
        )
        local_end = timezone.localize(
            datetime.datetime.combine(
                end_date + datetime.timedelta(days=1), datetime.time.min
            )
        )
        return timezone, local_start, local_end

    def _get_absence_lines(
        self, employee, leaves, start_date, end_date, local_start, local_end
    ):
        absence_lines = []
        ordinary_leaves = leaves.filtered(
            lambda leave: leave.holiday_status_id.request_unit
            not in ("natural_day", "natural_day_half_day")
        )
        natural_leaves = leaves - ordinary_leaves

        calendar = (
            employee.resource_calendar_id or employee.company_id.resource_calendar_id
        )
        if ordinary_leaves and calendar:
            intervals = employee.sudo().list_leaves(
                local_start,
                local_end,
                calendar=calendar,
                domain=[("holiday_id", "in", ordinary_leaves.ids)],
            )
            grouped_intervals = defaultdict(float)
            for day, hours, calendar_leave in intervals:
                leave = calendar_leave.holiday_id
                if leave in ordinary_leaves:
                    grouped_intervals[(day, leave.id)] += hours
            for (day, leave_id), hours in grouped_intervals.items():
                leave = ordinary_leaves.browse(leave_id)
                absence_lines.append(self._absence_line(leave, day, hours))

        for leave in natural_leaves:
            day = max(leave.request_date_from, start_date)
            last_day = min(leave.request_date_to, end_date)
            while day <= last_day:
                absence_lines.append(self._absence_line(leave, day))
                day += datetime.timedelta(days=1)

        return absence_lines

    @api.model
    def _absence_line(self, leave, day, hours=0):
        return {
            "kind": "absence",
            "date": day,
            "type": leave.holiday_status_id.display_name,
            "check_in": False,
            "check_out": False,
            "check_in_local": False,
            "check_out_local": False,
            "worked_hours": 0,
            "absence_hours": round(hours, 2),
            "leave_id": leave.id,
        }

    def _generate_employee_data(
        self, employees, start_date, end_date, include_absences=True
    ):
        """Generate timezone-aware attendance and approved absence data."""
        include_absences = include_absences and self._has_hr_holidays()
        employee_info_list = []
        boundaries = {
            employee.id: self._employee_month_bounds(employee, start_date, end_date)
            for employee in employees
        }
        utc_starts = [bounds[1].astimezone(pytz.utc) for bounds in boundaries.values()]
        utc_ends = [bounds[2].astimezone(pytz.utc) for bounds in boundaries.values()]
        search_start = min(utc_starts).replace(tzinfo=None) if utc_starts else False
        search_end = max(utc_ends).replace(tzinfo=None) if utc_ends else False

        all_attendances = (
            self.env["hr.attendance"].search(
                [
                    ("employee_id", "in", employees.ids),
                    ("check_in", ">=", search_start),
                    ("check_in", "<", search_end),
                ],
                order="employee_id, check_in",
            )
            if employees
            else self.env["hr.attendance"]
        )

        approved_leaves = False
        if include_absences and employees:
            allowed_employee_ids = employees.filtered(
                lambda employee: employee.company_id in self.env.companies
            ).ids
            approved_leaves = (
                self.env["hr.leave"]
                .sudo()
                .search(
                    [
                        ("employee_id", "in", allowed_employee_ids),
                        ("state", "=", "validate"),
                        ("active", "=", True),
                        ("holiday_status_id.time_type", "=", "leave"),
                        ("request_date_from", "<=", end_date),
                        ("request_date_to", ">=", start_date),
                    ]
                )
            )

        # Group attendances by employee_id
        attendances_by_employee = {}
        for att in all_attendances:
            attendances_by_employee.setdefault(att.employee_id.id, []).append(att)

        for emp in employees:
            timezone, local_start, local_end = boundaries[emp.id]
            emp_attendances = [
                attendance
                for attendance in attendances_by_employee.get(emp.id, [])
                if local_start
                <= pytz.utc.localize(attendance.check_in).astimezone(timezone)
                < local_end
            ]
            emp_sudo = emp.sudo()

            # Process attendance records
            attendance_data = []
            total_hours = 0
            dates_worked = set()  # Use set to count unique dates

            for att in emp_attendances:
                worked_hours = round(att.worked_hours or 0, 2)
                total_hours += worked_hours
                check_in_local = (
                    pytz.utc.localize(att.check_in)
                    .astimezone(timezone)
                    .replace(tzinfo=None)
                )
                check_out_local = (
                    pytz.utc.localize(att.check_out)
                    .astimezone(timezone)
                    .replace(tzinfo=None)
                    if att.check_out
                    else False
                )

                # Add to unique dates if check_in exists
                if att.check_in:
                    dates_worked.add(check_in_local.date())

                attendance_data.append(
                    {
                        "kind": "attendance",
                        "type": _("Attendance"),
                        "check_in": att.check_in,
                        "check_out": att.check_out,
                        "check_in_local": check_in_local,
                        "check_out_local": check_out_local,
                        "worked_hours": worked_hours,
                        "date": check_in_local.date(),
                    }
                )

            absence_data = (
                self._get_absence_lines(
                    emp,
                    approved_leaves.filtered(
                        lambda leave, employee=emp: leave.employee_id == employee
                    ),
                    start_date,
                    end_date,
                    local_start,
                    local_end,
                )
                if include_absences
                else []
            )
            lines = attendance_data + absence_data
            lines.sort(
                key=lambda line: (
                    line["date"],
                    0 if line["kind"] == "absence" else 1,
                    line["check_in_local"] or datetime.datetime.min,
                )
            )

            # Compile employee information (use sudo consistently for restricted fields)
            employee_info = {
                "emp_id": emp.id,
                "emp_name": emp.name or "N/A",
                "emp_code": (
                    emp_sudo.identification_id or emp_sudo.barcode or str(emp.id)
                ),
                "emp_identification": emp_sudo.identification_id or "N/A",
                "company_vat": emp.company_id.vat or "N/A",
                "company_name": emp.company_id.name or "N/A",
                "manager": emp.parent_id.name if emp.parent_id else "N/A",
                "department": emp.department_id.name if emp.department_id else "N/A",
                "job_title": emp_sudo.job_id.name if emp_sudo.job_id else "N/A",
                "attendances": attendance_data,
                "absences": absence_data,
                "lines": lines,
                "total_hours": round(total_hours, 2),
                "total_days": len(dates_worked),
                "avg_hours_per_day": round(total_hours / len(dates_worked), 2)
                if dates_worked
                else 0,
            }

            employee_info_list.append(employee_info)

        return employee_info_list
