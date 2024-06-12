# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.osv import expression

_logger = logging.getLogger(__name__)


def _daterange(start_date, end_date):
    """Return list of dates."""
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def get_attendances(self, employees, start_date, end_date):
    """Group attendances by user and day."""

    # Data mappings
    dates = {}
    attendances_data = {}
    summary = {}

    # Iterate on users
    for employee in employees:
        # Get statics
        hours_per_day = employee.resource_calendar_id.hours_per_day
        fixed_work_hours = False if hours_per_day == 0 else True
        company_hours_per_day = employee.company_id.resource_calendar_id.hours_per_day

        # Log time range
        dates[employee.id] = {}
        dates[employee.id]["start_date"] = start_date
        dates[employee.id]["end_date"] = end_date - timedelta(days=1)

        # Get all attendances and overtime in range
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", employee.id),
                "&",
                ("check_in", "<=", end_date),
                ("check_out", ">=", start_date),
            ]
        )
        overtimes = self.env["hr.attendance.overtime"].search(
            [
                ("employee_id", "=", employee.id),
                "&",
                ("date", "<=", end_date),
                ("date", ">=", start_date),
            ]
        )

        # Get leaves with from or to date in range
        from_domain = [("date_from", ">=", start_date), ("date_from", "<=", end_date)]
        to_domain = [("date_to", ">=", end_date), ("date_to", "<=", end_date)]
        domain = [
            ("calendar_id", "=", employee.resource_calendar_id.id),
            ("resource_id", "=", employee.resource_id.id),
        ]
        filters = expression.AND([domain, expression.OR([from_domain, to_domain])])
        leaves = self.env["resource.calendar.leaves"].search(filters)
        leave_hours = sum(leaves.holiday_id.mapped("number_of_hours_display"))

        # Update summary
        summary[employee.id] = {
            "fixed_work_hours": fixed_work_hours,
            "leave_hours": round(leave_hours, 2),
            "worked_hours": round(sum(attendances.mapped("worked_hours")), 2),
            "overtime_total": round(employee.total_overtime, 2),
        }

        # For each date in range compute details
        attendances_data[employee.id] = []
        planned_hours = 0
        overtime = 0
        for date in _daterange(start_date, end_date):
            # Get work hours
            min_check_date = datetime.combine(date, time.min)
            max_check_date = datetime.combine(date, time.max)
            work_hours = employee.resource_calendar_id.get_work_hours_count(
                min_check_date, max_check_date, True
            )
            planned_hours += work_hours

            # Get leave hours for this date
            active_leaves = leaves.filtered(
                lambda leave,
                date=date,
                min_check_date=min_check_date,
                max_check_date=max_check_date: leave.date_from < date < leave.date_to
                or min_check_date <= leave.date_from <= max_check_date
                or min_check_date <= leave.date_to <= max_check_date
            )

            # Set leave hours
            leave_hours = 0.0
            if active_leaves.holiday_id:
                number_of_hours = active_leaves.holiday_id.number_of_hours_display
                if number_of_hours > company_hours_per_day:
                    leave_hours = work_hours
                else:
                    leave_hours = number_of_hours

            # Get attendance hours for this date
            worked_hours = sum(
                attendances.filtered(
                    lambda attendance,
                    min_date=min_check_date,
                    max_date=max_check_date: min_date < attendance.check_in < max_date
                ).mapped("worked_hours")
            )

            # Get overtime hours for this date
            overtime_hours = sum(
                overtimes.filtered(lambda o, date=date: o.date == date.date()).mapped(
                    "duration"
                )
            )
            overtime += overtime_hours

            # Create data entry
            attendances_data[employee.id].append(
                {
                    "date": date,
                    "planned_hours": round(work_hours, 2),
                    "leave_hours": round(leave_hours, 2),
                    "worked_hours": round(worked_hours, 2),
                    "overtime": round(overtime_hours, 2),
                    "background_color": "lightgrey"
                    if work_hours == 0 and fixed_work_hours
                    else "none",
                }
            )

        # Update summary
        summary[employee.id]["planned_hours"] = round(planned_hours, 2)
        summary[employee.id]["overtime"] = round(overtime, 2)

    return dates, attendances_data, summary


def get_leave_allocations(self, employees):
    """Get data on leave and allocations."""

    # Data mappings
    leave_allocations = {}

    # Init statics
    now = fields.Datetime.now()

    # Iterate on users
    for employee in employees:
        # Get active allocations
        allocations = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "=", employee.id),
                "|",
                ("date_to", ">=", now),
                ("date_from", "<=", now),
            ]
        )

        leave_allocations[employee.id] = allocations

    return leave_allocations


def _get_report_values(self, docids, data=None, report_name=None):
    now = fields.Datetime.now()
    # Last month default dates
    start_date = now + relativedelta(months=-1, day=1, hour=0, minute=0, second=0)
    end_date = now + relativedelta(day=1, hour=0, minute=0, second=0)
    # Current month default dates
    # start_date = now + relativedelta(day=1, hour=0, minute=0, second=0)
    # end_date = now + relativedelta(month=5, day=1, hour=0, minute=0, second=0)

    # Check data for params from dialog
    if data and data.get("date_from"):
        start_date = datetime.strptime(data["date_from"], "%Y-%m-%d")
    if data and data.get("date_until"):
        end_date = datetime.strptime(data["date_until"], "%Y-%m-%d") + timedelta(days=1)
    if data.get("context", {}).get("active_ids"):
        docids = data["context"]["active_ids"]

    # Browse documents
    if report_name == "report.hr_employee_attendance_report.res_users":
        employees = self.env["res.users"].browse(docids).mapped("employee_id")
    else:
        employees = self.env["hr.employee"].browse(docids)

    dates, attendances, summary = get_attendances(self, employees, start_date, end_date)
    leave_allocations = get_leave_allocations(self, employees)

    return {
        "doc_ids": docids,
        "doc_model": "hr.employee",
        "docs": employees,
        "dates": dates,
        "attendances": attendances,
        "summary": summary,
        "leave_allocations": leave_allocations,
    }
