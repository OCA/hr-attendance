from odoo import _
from odoo.exceptions import UserError
from odoo.http import request, route

from odoo.addons.hr_attendance.controllers.main import HrAttendance


class GeoAttendanceController(HrAttendance):
    @route("/hr_attendance/systray_check_in_out", type="json", auth="user")
    def systray_attendance(self, latitude=False, longitude=False):
        employee = request.env.user.employee_id

        if not employee:
            return super().systray_attendance(latitude=latitude, longitude=longitude)

        ok, _zone = employee._is_inside_any_allowed_location(latitude, longitude)

        if not ok:
            raise UserError(
                _(
                    "You are outside an authorized area for clocking in."
                    "Create a new area or go to an authorized zone."
                )
            )

        if request.params.get("attendance_reason_id"):
            request.update_context(
                attendance_reason_id=int(request.params.get("attendance_reason_id"))
            )

        return super().systray_attendance(latitude=latitude, longitude=longitude)
