# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_overtime = fields.Boolean(
        string="Overtime",
        default=False,
    )

    def _add_reason_by_code(self, code):
        self.ensure_one()
        reason = self.env["hr.attendance.reason"].search([("code", "=", code)], limit=1)
        self.attendance_reason_ids += reason

    def _get_worktimes(self):
        """get the heroical worktime for the check_in date"""
        worktimes = self.employee_id._get_worktimes(self.check_in)
        return worktimes["current"] | worktimes["next"]

    def needs_autoclose(self):
        """Overwrite methode from hr_attendance_autoclose to determine if
        line should be closed according the end line work time"""
        self.ensure_one()
        worktime = self._get_worktimes()
        if worktime and fields.Datetime.now() > worktime[0]._get_datetime_from_field(
            self.check_in, "hour_check_out_to"
        ):
            return not self.employee_id.no_autoclose
        # following case use hr_attendance_autoclose rules:
        # * task running on sunday
        # * no worktime found at the begining of the current attendance
        #   (starts working at the end of the day)
        return super().needs_autoclose()

    def autoclose_attendance(self, reason):
        self.ensure_one()
        worktime = self._get_worktimes()
        if worktime:
            attendances = self.employee_id._attendance_action_change()
            res = attendances.write({"attendance_reason_ids": [(4, reason.id)]})
        else:
            res = super().autoclose_attendance(reason)
            self.is_overtime = True
        return res
