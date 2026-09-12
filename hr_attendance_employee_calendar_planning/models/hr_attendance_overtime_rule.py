# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAttendanceOvertimeRule(models.Model):
    _inherit = "hr.attendance.overtime.rule"

    def _get_expected_hours_from_contract(self, date, version, period="day"):
        # It is important to define the appropriate context keys so that the value is
        # as expected.
        self = self.with_context(
            flexible_hours_from_date=date,
            flexible_hours_to_date=date,
        )
        version.resource_calendar_id._compute_hours_per_week()
        return super()._get_expected_hours_from_contract(
            date=date, version=version, period=period
        )

    def _generate_overtime_vals_v2(
        self, min_check_in, max_check_out, attendances, schedules_intervals_by_employee
    ):
        # It is important to define the appropriate context keys so that the value is
        # as expected.
        attendances = attendances.with_context(
            flexible_hours_from_date=fields.Datetime.context_timestamp(
                self, min_check_in
            ).date(),
            flexible_hours_to_date=fields.Datetime.context_timestamp(
                self, max_check_out
            ).date(),
        )
        attendances.mapped("employee_id").resource_calendar_id._compute_flexible_hours()
        return super()._generate_overtime_vals_v2(
            min_check_in, max_check_out, attendances, schedules_intervals_by_employee
        )

    def _get_daterange_overtime_undertime_intervals_for_quantity_rule(
        self, start, stop, attendance_intervals, schedule
    ):
        # It is important to define the appropriate context keys so that the value is
        # as expected.
        self = self.with_context(
            flexible_hours_from_date=fields.Datetime.context_timestamp(
                self, start
            ).date(),
            flexible_hours_to_date=fields.Datetime.context_timestamp(self, stop).date(),
        )
        employees = self.env["hr.employee"]
        for _a_start, _a_stop, attendance in attendance_intervals:
            employees += attendance.employee_id
        employees.resource_calendar_id._compute_flexible_hours()
        return super()._get_daterange_overtime_undertime_intervals_for_quantity_rule(
            start, stop, attendance_intervals, schedule
        )
