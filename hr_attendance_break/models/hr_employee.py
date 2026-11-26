# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_open_attendance_break(self):
        self.ensure_one()
        return (
            self.env["hr.attendance.break"]
            .sudo()
            .search(
                [("employee_id", "=", self.id), ("break_stop", "=", False)],
                limit=1,
            )
        )

    def _attendance_action_change(self, geo_information=None):
        """Start and end breaks through the check out / check in buttons.

        Checking out with a reason linked to a break type starts a break. The
        next check in ends the break and reopens the same attendance, so the
        break stays inside the attendance. A break left open on a previous day
        is discarded and a new attendance is started as usual.
        """
        self.ensure_one()
        open_break = self._get_open_attendance_break()
        if open_break:
            attendance = open_break.attendance_id
            if self._is_attendance_break_resumable(open_break):
                now = fields.Datetime.now()
                open_break.break_stop = now
                attendance.check_out = False
                reason_id = self.env.context.get("attendance_reason_id")
                if reason_id:
                    attendance.attendance_reason_ids = [(4, reason_id)]
                return attendance
            open_break.unlink()
        attendance = super()._attendance_action_change(geo_information=geo_information)
        reason = self.env["hr.attendance.reason"].browse(
            self.env.context.get("attendance_reason_id")
        )
        if attendance.check_out and reason.break_type_id:
            self.env["hr.attendance.break"].sudo().create(
                {
                    "attendance_id": attendance.id,
                    "break_type_id": reason.break_type_id.id,
                    "break_start": attendance.check_out,
                }
            )
        return attendance

    def _is_attendance_break_resumable(self, attendance_break):
        """Whether checking in ends the break and reopens its attendance.

        Only breaks started on the same day, in the employee's timezone, are
        resumed. A break that was never ended (e.g. the employee went home)
        must not reopen yesterday's attendance.
        """
        attendance = attendance_break.attendance_id
        if attendance.check_out != attendance_break.break_start:
            # The attendance has been modified since the break started
            return False
        tz = self.tz or "UTC"
        start = fields.Datetime.context_timestamp(
            self.with_context(tz=tz), attendance_break.break_start
        )
        now = fields.Datetime.context_timestamp(
            self.with_context(tz=tz), fields.Datetime.now()
        )
        return start.date() == now.date()
