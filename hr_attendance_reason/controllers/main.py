# Copyright 2024 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request, route

from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendance(HrAttendance):
    # inherited routes
    @route("/hr_attendance/attendance_user_data", type="json", auth="user")
    def user_attendance_data(self):
        response = super().user_attendance_data()
        # try to get the company of the employee to show the correct reasons from
        # the employees company
        company = (
            request.env.user.employee_id.company_id
            if request.env.user.employee_id
            else request.env.company
        )
        response.update(self._get_attendance_reason_settings(company))
        # get available reasons for employee company
        reasons = []
        if response.get("attendance_state", False):
            if response.get("attendance_state", False) == "checked_out":
                action_type = "sign_in"
            else:
                action_type = "sign_out"
            reasons = self._get_attendance_reasons(action_type, company)
        response.update({"reasons": reasons})
        return response

    @route("/hr_attendance/systray_check_in_out", type="json", auth="user")
    def systray_attendance(self, latitude=False, longitude=False):
        if request.params.get("attendance_reason_id"):
            request.update_context(
                attendance_reason_id=int(request.params.get("attendance_reason_id"))
            )
        return super().systray_attendance(latitude=latitude, longitude=longitude)

    @http.route("/hr_attendance/manual_selection", type="json", auth="public")
    def manual_selection_with_geolocation(
        self, token, employee_id, pin_code, latitude=False, longitude=False
    ):
        if request.params.get("attendance_reason_id"):
            request.update_context(
                attendance_reason_id=int(request.params.get("attendance_reason_id"))
            )
        return super().manual_selection_with_geolocation(
            token, employee_id, pin_code, latitude, longitude
        )

    # new routes
    @route("/hr_attendance_reason/get_reasons", type="json", auth="public")
    def attendance_get_reasons(self, token, employee_id, pin_code):
        company = self._get_company(token)
        if company:
            employee = request.env["hr.employee"].sudo().browse(employee_id)
            if employee.company_id == company and (
                (not company.attendance_kiosk_use_pin) or (employee.pin == pin_code)
            ):
                res = self._get_employee_info_response(employee)
                action_type = (
                    "sign_out"
                    if res.get("attendance_state") == "checked_in"
                    else "sign_in"
                )
                res.update(
                    {
                        "reasons": self._get_attendance_reasons(action_type, company),
                        **self._get_attendance_reason_settings(company),
                    }
                )
                return res
        return {}

    @route("/hr_attendance_reason/reason_settings", type="json", auth="public")
    def kiosk_reason_settings(self, token):
        company = self._get_company(token)
        if company:
            return self._get_attendance_reason_settings(company)
        return {}

    def _get_attendance_reason_settings(self, company):
        show_reason = company.show_reason_on_attendance_screen
        required_reason = company.required_reason_on_attendance_screen
        default_sign_in_reason_id = (
            company.reason_on_attendance_screen_default_sign_in.id
        )
        default_sign_out_reason_id = (
            company.reason_on_attendance_screen_default_sign_out.id
        )
        return {
            "show_reason_on_attendance_screen": show_reason,
            "required_reason_on_attendance_screen": required_reason,
            "default_sign_in_reason_id": default_sign_in_reason_id,
            "default_sign_out_reason_id": default_sign_out_reason_id,
        }

    def _get_attendance_reasons(self, action_type, company):
        """
        Get the attendance reasons to show on the attendance screen.
        :param action_type: sign_in or sign_out.
        """
        AttendanceReason = request.env["hr.attendance.reason"].sudo()
        return AttendanceReason.search_read(
            domain=[
                ("show_on_attendance_screen", "=", True),
                ("action_type", "=", action_type),
                ("company_id", "in", [False, company.id]),
            ],
            fields=["name", "action_type"],
        )
