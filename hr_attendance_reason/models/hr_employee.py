# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_reason_snapshot(self):
        """Return the data needed to know if a check in/out happens afterwards."""
        last_attendance = self.last_attendance_id
        return last_attendance, last_attendance.check_out

    def _attendance_reason_apply(self, reason_id, snapshot):
        """Add the reason to the attendance created or closed since the snapshot.

        Core returns a notification (not the attendance), and may do nothing at
        all (single check-in), so only tag the attendance if it changed.
        """
        attendance = self.last_attendance_id
        last_attendance, last_check_out = snapshot
        if not reason_id or (
            attendance == last_attendance and attendance.check_out == last_check_out
        ):
            return
        # Never trust the id sent by the client: same filters as the screen
        try:
            reason_id = int(reason_id)
        except (TypeError, ValueError):
            return
        reason = (
            self.env["hr.attendance.reason"]
            .sudo()
            .search(
                [
                    ("id", "=", reason_id),
                    ("show_on_attendance_screen", "=", True),
                    (
                        "action_type",
                        "=",
                        "sign_out" if attendance.check_out else "sign_in",
                    ),
                    ("company_id", "in", [False, self.company_id.id]),
                ],
                limit=1,
            )
        )
        if reason:
            attendance.attendance_reason_ids = [(4, reason.id)]

    def _attendance_action_change(self, geo_information=None, check_in_image_data=None):
        snapshot = self._attendance_reason_snapshot()
        notification = super()._attendance_action_change(
            geo_information=geo_information, check_in_image_data=check_in_image_data
        )
        self._attendance_reason_apply(
            self.env.context.get("attendance_reason_id"), snapshot
        )
        return notification
