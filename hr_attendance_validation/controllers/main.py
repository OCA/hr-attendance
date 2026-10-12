from odoo.tools import float_round

from odoo.addons.hr_attendance_overtime.controllers.main import HrAttendanceOvertime


class HrAttendanceValidation(HrAttendanceOvertime):
    @staticmethod
    def _get_user_attendance_data(employee):
        response = super(
            HrAttendanceValidation, HrAttendanceValidation
        )._get_user_attendance_data(employee)
        if employee:
            response["hours_current_week"] = float_round(
                employee.hours_current_week, precision_digits=2
            )
        return response
