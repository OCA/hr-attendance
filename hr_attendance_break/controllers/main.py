# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo.http import request, route

from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendance(HrAttendance):
    @route("/hr_attendance/attendance_user_data", type="jsonrpc", auth="user")
    def user_attendance_data(self):
        response = super().user_attendance_data()
        employee = request.env.user.employee_id
        if employee:
            response.update(employee._get_attendance_break_data())
        return response

    @route("/hr_attendance/toggle_break", type="jsonrpc", auth="user")
    def toggle_break(self):
        """Start or end a break for the current user, then return the refreshed
        attendance payload so the systray can update its label."""
        employee = request.env.user.employee_id
        if employee:
            employee.attendance_toggle_break()
        return self.user_attendance_data()

    # Public kiosk routes
    def _kiosk_break_employee(self, token, employee_id, pin_code):
        """Return the kiosk employee if the token/company/pin check out."""
        company = self._get_company(token)
        if not company:
            return request.env["hr.employee"]
        employee = request.env["hr.employee"].sudo().browse(employee_id)
        if employee.company_id == company and (
            (not company.attendance_kiosk_use_pin) or employee.pin == pin_code
        ):
            return employee
        return request.env["hr.employee"]

    @route("/hr_attendance_break/employee_state", type="jsonrpc", auth="public")
    def kiosk_break_employee_state(self, token, employee_id, pin_code=False):
        """Tell the kiosk whether the employee is checked in / on a break, so it
        can offer a break instead of checking them straight out."""
        employee = self._kiosk_break_employee(token, employee_id, pin_code)
        if not employee:
            return {}
        return {
            "employee_name": employee.name,
            "checked_in": employee.attendance_state == "checked_in",
            **employee._get_attendance_break_data(),
        }

    @route("/hr_attendance_break/toggle_break_kiosk", type="jsonrpc", auth="public")
    def kiosk_toggle_break(self, token, employee_id, pin_code=False):
        employee = self._kiosk_break_employee(token, employee_id, pin_code)
        if not employee:
            return {}
        employee.attendance_toggle_break()
        response = self._get_employee_info_response(employee)
        response.update(employee._get_attendance_break_data())
        return response
