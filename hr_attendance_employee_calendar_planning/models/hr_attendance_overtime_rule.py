# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAttendanceOvertimeRule(models.Model):
    _inherit = "hr.attendance.overtime.rule"

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
        return super()._generate_overtime_vals_v2(
            min_check_in, max_check_out, attendances, schedules_intervals_by_employee
        )
