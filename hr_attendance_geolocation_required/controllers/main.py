# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, http

from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendanceCustom(HrAttendance):
    @http.route()
    def manual_selection_with_geolocation(
        self, token, employee_id, pin_code, latitude=False, longitude=False
    ):
        company = (
            http.request.env["res.company"]
            .sudo()
            .search([("attendance_kiosk_key", "=", token)], limit=1)
        )
        if company.attendance_geolocation_required and (not latitude or not longitude):
            return {"error": _("You must activate location and GPS to clock in.")}

        return super().manual_selection_with_geolocation(
            token, employee_id, pin_code, latitude=latitude, longitude=longitude
        )
