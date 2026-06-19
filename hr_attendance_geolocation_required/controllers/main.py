# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, http
from odoo.http import request


class HrAttendanceCustom(http.Controller):
    @http.route(
        "/hr_attendance/manual_selection",
        type="json",
        auth="public",
        website=True,
        csrf=False,
    )
    def manual_selection(
        self, employee_id, pin_code=None, latitude=False, longitude=False
    ):
        if request.env.company.attendance_geolocation_required and (
            not latitude or not longitude
        ):
            return {"error": _("You must activate location and GPS to clock in.")}

        employee = request.env["hr.employee"].sudo().browse(employee_id)
        if not employee.exists():
            return {"error": _("Invalid employee.")}

        ctx = request.env.context.copy()
        ctx.update({"latitude": latitude, "longitude": longitude})
        return employee.with_context(**ctx).attendance_manual(
            "hr_attendance.hr_attendance_action_kiosk_mode", pin_code
        )
