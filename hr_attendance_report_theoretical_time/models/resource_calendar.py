# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch_exclude_public_holidays(
        self, start_dt, end_dt, intervals, resources, tz
    ):
        partner_id = self.env.context.get("partner_id", False)
        employee_id = self.env.context.get("employee_id", False)
        if not partner_id and employee_id:
            employee = self.env["hr.employee"].browse(employee_id)
            self = self.with_context(partner_id=employee.address_id.id)
        return super()._attendance_intervals_batch_exclude_public_holidays(
            start_dt, end_dt, intervals, resources, tz
        )

    def _get_attendance_intervals_days_data(self, attendance_intervals):
        use_actual_hours = (
            self.env.context.get("use_actual_interval_hours_for_flexible_calendar")
            and len(self) == 1
            and self.flexible_hours
        )
        if not use_actual_hours:
            return super()._get_attendance_intervals_days_data(attendance_intervals)
        intervals = list(attendance_intervals)
        result = super()._get_attendance_intervals_days_data(intervals)
        result["hours"] = sum(
            (stop - start).total_seconds() / 3600 for start, stop, _meta in intervals
        )
        return result
