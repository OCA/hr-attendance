# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, modules


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _test_module_hr_attendance_employee_calendar_planning(self):
        condition = super()._test_module_hr_attendance_employee_calendar_planning()
        condition_extra = not modules.module.current_test or (
            modules.module.current_test
            and modules.module.current_test.test_module
            == "hr_attendance_employee_calendar_planning"
        )
        return condition or condition_extra
