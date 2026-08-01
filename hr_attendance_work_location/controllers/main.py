# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _
from odoo.http import request, route

from odoo.addons.hr_attendance.controllers.main import HrAttendance as CoreHrAttendance


class HrAttendance(CoreHrAttendance):
    def _assign_work_location(self, attendance, work_location_id):
        work_location = request.env["hr.work.location"].sudo().browse(work_location_id)
        if not work_location.exists():
            return
        if work_location.exclude_from_attendance:
            return
        if work_location.company_id != attendance.company_id:
            return
        if not attendance.check_out:
            attendance.in_work_location_id = work_location.id
        else:
            attendance.out_work_location_id = work_location.id

    def _validate_work_location_required(self, company, work_location_id):
        if company.work_location_required and not work_location_id:
            employee = request.env.user.employee_id
            if employee and employee.attendance_state == "checked_in":
                return False
            return {
                "error": "work_location_required",
                "message": _("Work location is required."),
            }
        return False

    @route(
        "/hr_attendance_work_location/attendance_preflight", type="json", auth="public"
    )
    def attendance_preflight(self, token, barcode=None, employee_id=None):
        company = self._get_company(token)
        if not company:
            return {}
        if company.work_location_mode != "manual":
            return {}
        employee = None
        if barcode:
            employee = (
                request.env["hr.employee"]
                .sudo()
                .search(
                    [("barcode", "=", barcode), ("company_id", "=", company.id)],
                    limit=1,
                )
            )
        elif employee_id:
            employee = request.env["hr.employee"].sudo().browse(employee_id)
            if employee.company_id != company:
                employee = None
        if not employee:
            return {}
        return {
            "employee_id": employee.id,
            "employee_name": employee.name,
            "attendance_state": employee.attendance_state,
            "work_locations": [
                {"id": loc.id, "name": loc.name}
                for loc in request.env["hr.work.location"]
                .sudo()
                .search(
                    [
                        ("company_id", "=", company.id),
                        ("exclude_from_attendance", "=", False),
                    ]
                )
            ],
            "work_location_required": company.work_location_required,
            "default_work_location_id": company.manual_work_location_id.id or False,
        }

    @route(
        "/hr_attendance_work_location/barcode_with_location", type="json", auth="public"
    )
    def barcode_with_location(self, token, barcode, work_location_id=False):
        company = self._get_company(token)
        if not company:
            return {}
        error = self._validate_work_location_required(company, work_location_id)
        if error:
            return error
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search(
                [("barcode", "=", barcode), ("company_id", "=", company.id)], limit=1
            )
        )
        if employee:
            attendance = employee._attendance_action_change(
                self._get_geoip_response("kiosk")
            )
            if work_location_id:
                self._assign_work_location(attendance, work_location_id)
            return self._get_employee_info_response(employee)
        return {}

    @route(
        "/hr_attendance_work_location/kiosk_location_settings",
        type="json",
        auth="public",
    )
    def kiosk_location_settings(self, token):
        company = self._get_company(token)
        if not company:
            return {}
        return {
            "work_location_mode": company.work_location_mode,
            "work_location_required": company.work_location_required,
            "default_work_location_id": company.manual_work_location_id.id or False,
            "work_locations": [
                {"id": loc.id, "name": loc.name}
                for loc in request.env["hr.work.location"]
                .sudo()
                .search(
                    [
                        ("company_id", "=", company.id),
                        ("exclude_from_attendance", "=", False),
                    ]
                )
            ],
        }

    @route("/hr_attendance/manual_selection", type="json", auth="public")
    def manual_selection_with_geolocation(
        self,
        token,
        employee_id,
        pin_code,
        latitude=False,
        longitude=False,
        work_location_id=False,
    ):
        company = self._get_company(token)
        if company:
            error = self._validate_work_location_required(company, work_location_id)
            if error:
                return error
            employee = request.env["hr.employee"].sudo().browse(employee_id)
            if employee.company_id == company and (
                not company.attendance_kiosk_use_pin or employee.pin == pin_code
            ):
                attendance = employee.sudo()._attendance_action_change(
                    self._get_geoip_response(
                        "kiosk", latitude=latitude, longitude=longitude
                    )
                )
                if work_location_id:
                    self._assign_work_location(attendance, work_location_id)
                return self._get_employee_info_response(employee)
        return {}

    @route("/hr_attendance/systray_check_in_out", type="json", auth="user")
    def systray_attendance(
        self, latitude=False, longitude=False, work_location_id=False
    ):
        employee = request.env.user.employee_id
        company = employee.company_id
        error = self._validate_work_location_required(company, work_location_id)
        if error:
            return error
        geo_ip_response = self._get_geoip_response(
            mode="systray", latitude=latitude, longitude=longitude
        )
        attendance = employee._attendance_action_change(geo_ip_response)
        if work_location_id:
            self._assign_work_location(attendance, work_location_id)
        return self._get_employee_info_response(employee)

    def _get_employee_info_response(self, employee):
        response = super()._get_employee_info_response(employee)
        if employee.attendance_state == "checked_in":
            attendance = employee.last_attendance_id.sudo()
            if attendance and attendance.in_work_location_id:
                response["in_work_location_name"] = attendance.in_work_location_id.name
        return response
