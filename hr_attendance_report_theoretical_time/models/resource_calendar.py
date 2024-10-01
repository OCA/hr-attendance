# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.resource.models.resource_resource import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch_exclude_public_holidays(
        self, start_dt, end_dt, intervals, resources, tz
    ):
        partner_id = self.env.context.get("partner_id", False)
        if not partner_id:
            employee_id = self.env.context.get("employee_id", False)
            if employee_id:
                employee = self.env["hr.employee"].browse(employee_id)
                partner_id = employee.address_id.id
            list_by_dates = (
                self.env["hr.holidays.public"]
                .get_holidays_list(
                    start_dt=start_dt.date(),
                    end_dt=end_dt.date(),
                    partner_id=partner_id,
                )
                .mapped("date")
            )
            for resource in resources:
                interval_resource = intervals[resource.id]
                attendances = []
                for attendance in interval_resource._items:
                    if attendance[0].date() not in list_by_dates:
                        attendances.append(attendance)
                intervals[resource.id] = Intervals(attendances)
            return intervals
        return super()._attendance_intervals_batch_exclude_public_holidays(
            start_dt, end_dt, intervals, resources, tz
        )
