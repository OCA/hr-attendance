# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_open_attendance(self):
        self.ensure_one()
        return self.env["hr.attendance"].search(
            [("employee_id", "=", self.id), ("check_out", "=", False)],
            limit=1,
        )

    def _attendance_action_change(self, geo_information=None):
        # An open attendance means this action checks the employee OUT, so close
        # any still-running break before the attendance is closed.
        for employee in self:
            open_attendance = employee._get_open_attendance()
            if open_attendance:
                open_attendance._close_open_breaks()
        return super()._attendance_action_change(geo_information=geo_information)

    def attendance_toggle_break(self):
        """Toggle the break for the employee's currently open attendance."""
        self.ensure_one()
        open_attendance = self._get_open_attendance()
        if not open_attendance:
            raise UserError(self.env._("You must be checked in to record a break."))
        return open_attendance.toggle_break()

    def _get_attendance_break_data(self):
        """Break-related payload merged into the systray attendance data."""
        self.ensure_one()
        open_attendance = self._get_open_attendance()
        on_break = bool(open_attendance and open_attendance.is_on_break)
        return {
            "on_break": on_break,
            "break_hours": open_attendance.break_hours if open_attendance else 0.0,
        }
