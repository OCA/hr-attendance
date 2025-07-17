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
