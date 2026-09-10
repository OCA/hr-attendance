# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @api.model
    def lazy_session_info(self):
        """Add the attendance reasons to the systray employee data.

        Since v19 the initial systray attendance data comes from the lazy
        session (which calls the core controller helper directly), not from
        the /hr_attendance/attendance_user_data route, so the reasons and
        their settings must be injected here as well.
        """
        res = super().lazy_session_info()
        attendance_data = res.get("attendance_user_data")
        employee = self.env.user.employee_id if self.env.user else None
        if attendance_data and employee:
            company = employee.company_id
            attendance_data.update(
                {
                    "show_reason_on_attendance_screen": (
                        company.show_reason_on_attendance_screen
                    ),
                    "required_reason_on_attendance_screen": (
                        company.required_reason_on_attendance_screen
                    ),
                    "default_sign_in_reason_id": (
                        company.reason_on_attendance_screen_default_sign_in.id
                    ),
                    "default_sign_out_reason_id": (
                        company.reason_on_attendance_screen_default_sign_out.id
                    ),
                    "reasons": self._get_attendance_screen_reasons(
                        attendance_data, company
                    ),
                }
            )
        return res

    def _get_attendance_screen_reasons(self, attendance_data, company):
        attendance_state = attendance_data.get("attendance_state")
        if not attendance_state:
            return []
        action_type = "sign_in" if attendance_state == "checked_out" else "sign_out"
        return (
            self.env["hr.attendance.reason"]
            .sudo()
            .search_read(
                domain=[
                    ("show_on_attendance_screen", "=", True),
                    ("action_type", "=", action_type),
                    ("company_id", "in", [False, company.id]),
                ],
                fields=["name", "action_type"],
            )
        )
