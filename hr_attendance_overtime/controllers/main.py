from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendanceOvertime(HrAttendance):
    @staticmethod
    def _get_user_attendance_data(employee):
        response = super(
            HrAttendanceOvertime, HrAttendanceOvertime
        )._get_user_attendance_data(employee)
        if employee:
            response["overtime_info"] = employee.todays_working_times()
        return response
