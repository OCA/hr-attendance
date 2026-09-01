# Copyright 2026 Tecnativa - Víctor Martínez
from collections import defaultdict

from odoo import models


class HrAattendance(models.Model):
    _inherit = "hr.attendance"

    def _get_worked_hours_in_range(self, start_dt, end_dt):
        # It is important to define the appropriate context keys so that the value is
        # as expected.
        self = self.with_context(
            flexible_hours_from_date=start_dt.date(),
            flexible_hours_to_date=end_dt.date(),
        )
        # TODO: Try to remove the call to that compute in hr_employee_calendar_planning
        self.employee_id._compute_is_flexible()
        return super()._get_worked_hours_in_range(start_dt, end_dt)

    def _update_overtime(self, employee_attendance_dates=None):
        """We need to accurately determine whether the schedule is flexible or not;
        therefore, we must add specific context keys and iterate through each record
        to do this correctly, since we may receive records for multiple employees.
        """
        if self.env.context.get("flexible_hours_from_date"):
            return super()._update_overtime()
        if not employee_attendance_dates:
            employee_attendance_dates = self._get_attendances_dates()
        for employee, attendance_dates in employee_attendance_dates.items():
            data_item = defaultdict(set)
            data_item[employee] = attendance_dates
            start_date = min(day for _datetime_date, day in attendance_dates)
            end_date = max(day for _datetime_date, day in attendance_dates)
            items = self.filtered(
                lambda x, employee=employee: x.exists() and x.employee_id == employee
            )
            items.with_context(
                flexible_hours_from_date=start_date,
                flexible_hours_to_date=end_date,
            )._update_overtime(data_item)
