# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime, time

from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

from odoo import SUPERUSER_ID, fields, models
from odoo.osv import expression


class HrEmployeeBase(models.Model):
    _inherit = "hr.employee"

    def todays_working_times(self):
        """Method used by my attendance/kiosk view in order
        to display employee planning and working times.

        :return: A dictionary containing the current state code, state message,
            theoretical work times for the day, and done attendances.
        :rtype: dict
        """
        self.ensure_one()
        employee = self
        now = fields.Datetime.now()
        tz = timezone(employee.tz)
        now_utc = utc.localize(now)
        now_tz = now_utc.astimezone(tz)
        start_tz = now_tz + relativedelta(
            hour=0, minute=0
        )  # day start in the employee's timezone
        start_naive = start_tz.astimezone(utc).replace(tzinfo=None)

        def dtime(worktime, field_name):
            return worktime._get_datetime_from_field(now, field_name)

        worktimes = employee._get_worktimes(now)
        state = ""
        if employee.attendance_state == "checked_in":
            state, __unused = employee._get_check_out_reason_code(now)
        else:
            state, __unused = employee._get_check_in_reason_code(now)

        reason = self.env["hr.attendance.reason"].search(
            [("code", "=", state)], limit=1
        )
        message = reason and reason.description or ""

        theoretical_work_times = []
        worktimes["previous"] = worktimes["previous"].sorted(
            key=lambda r: r.hour_check_in_from
        )
        all_worktimes = worktimes["previous"] | worktimes["current"] | worktimes["next"]
        current_time = start_naive
        for worktime in all_worktimes:
            check_in_from = dtime(worktime, "hour_check_in_from")
            check_out_to = dtime(worktime, "hour_check_out_to")
            if current_time < check_in_from:
                theoretical_work_times.append(
                    {
                        "start": current_time,
                        "end": check_in_from,
                        "hours": (check_in_from - current_time).seconds / 3600,
                        "is_worktime": False,
                    }
                )
                current_time = check_in_from

            theoretical_work_times.append(
                {
                    "start": current_time,
                    "end": check_out_to,
                    "hours": (check_out_to - current_time).seconds / 3600,
                    "is_worktime": True,
                }
            )
            current_time = check_out_to

        done_attendances = []
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", employee.id),
                ("check_in", "<=", now),
                "|",
                ("check_out", ">=", start_naive),
                ("check_out", "=", False),
            ],
            order="check_in",
        )
        current_time = start_naive
        for attendance in attendances:
            check_in = attendance.check_in
            check_out = attendance.check_out or now
            if current_time < check_in:
                done_attendances.append(
                    {
                        "start": current_time,
                        "end": check_in,
                        "hours": (check_in - current_time).seconds / 3600,
                        "is_worktime": False,
                    }
                )
                current_time = check_in

            done_attendances.append(
                {
                    "start": check_in,
                    "end": check_out,
                    "is_checked_out": True if attendance.check_out else False,
                    "hours": (check_out - check_in).seconds / 3600,
                    "is_worktime": True,
                }
            )
            current_time = check_out

        return {
            "state": state,
            "message": message,
            "theoretical_work_times": theoretical_work_times,
            "done_attendances": done_attendances,
        }

    def _get_worktimes(self, dt_utc_without_tz):
        """Retrieve the previous, current, and next theoretical work intervals
        for the employee based on their resource calendar for a given datetime.

        :param dt_utc_without_tz: The datetime to evaluate work schedules against
            (naive UTC).
        :type dt_utc_without_tz: datetime.datetime
        :return: A dictionary with keys 'previous', 'current', and 'next', each
            containing a recordset of `resource.calendar.attendance`.
        :rtype: dict
        """
        self.ensure_one()
        dt_utc = dt_utc_without_tz.replace(tzinfo=utc)
        tz = timezone(self.resource_calendar_id.tz)
        dt_calendar_tz = dt_utc.astimezone(tz)
        domain = [
            ("day_period", "!=", "lunch"),
            ("calendar_id", "=", self.resource_calendar_id.id),
            ("dayofweek", "=", str(dt_calendar_tz.weekday())),
            "|",
            ("date_from", "<=", dt_utc_without_tz.date()),
            ("date_from", "=", False),
            "|",
            ("date_to", ">=", dt_utc_without_tz.date()),
            ("date_to", "=", False),
            ("display_type", "=", False),
        ]

        tz_hour = (
            dt_calendar_tz
            - tz.localize(
                datetime.combine(
                    dt_calendar_tz.date(),
                    time(),
                )
            )
        ).total_seconds() / 3600
        domain_previous = expression.AND(
            [
                domain,
                [
                    ("hour_check_out_to", "<=", tz_hour),
                ],
            ]
        )
        domain_current = expression.AND(
            [
                domain,
                [
                    ("hour_check_in_from", "<=", tz_hour),
                    ("hour_check_out_to", ">", tz_hour),
                ],
            ]
        )
        domain_next = expression.AND(
            [
                domain,
                [
                    ("hour_check_in_from", ">", tz_hour),
                ],
            ]
        )
        WorkTime = self.env["resource.calendar.attendance"]
        return {
            "previous": WorkTime.search(
                domain_previous,
                order="hour_check_out_to desc",
            )
            or WorkTime,
            "current": WorkTime.search(
                domain_current,
                order="hour_check_in_from asc",
            )
            or WorkTime,
            "next": WorkTime.search(
                domain_next,
                order="hour_check_in_from asc",
            )
            or WorkTime,
        }

    def _get_check_in_reason_code(self, dt_utc_without_tz):
        """Determine the check-in reason code based on the expected work times
        for the given datetime.

        :param dt_utc_without_tz: The check-in datetime (naive UTC).
        :type dt_utc_without_tz: datetime.datetime
        :return: A tuple containing the check-in reason code (str) and the
            matched theoretical `resource.calendar.attendance` recordset.
        :rtype: tuple(str, recordset)
        """
        worktimes = self._get_worktimes(dt_utc_without_tz)
        current_or_next = worktimes["current"] | worktimes["next"]

        if current_or_next:
            date_check_in_from = current_or_next[0]._get_datetime_from_field(
                dt_utc_without_tz, "hour_check_in_from"
            )
            date_check_in_to = current_or_next[0]._get_datetime_from_field(
                dt_utc_without_tz, "hour_check_in_to"
            )
            if dt_utc_without_tz < date_check_in_from:
                return "CHECK-IN-EARLIER", current_or_next[0]
            elif date_check_in_from <= dt_utc_without_tz <= date_check_in_to:
                return "CHECK-IN-ONTIME", current_or_next[0]
            else:
                return "CHECK-IN-LATE", current_or_next[0]
        else:
            return "CHECK-IN-NO-NEXT", self.env["resource.calendar.attendance"]

    def _get_check_out_reason_code(self, dt_utc_without_tz):
        """Determine the check-out reason code based on the expected work times
        for the given datetime.

        :param dt_utc_without_tz: The check-out datetime (naive UTC).
        :type dt_utc_without_tz: datetime.datetime
        :return: A tuple containing the check-out reason code (str) and the
            matched theoretical `resource.calendar.attendance` recordset.
        :rtype: tuple(str, recordset)
        """
        worktimes = self._get_worktimes(dt_utc_without_tz)
        current_or_previous = worktimes["current"] | worktimes["previous"]

        if current_or_previous:
            date_check_out_from = current_or_previous[0]._get_datetime_from_field(
                dt_utc_without_tz, "hour_check_out_from"
            )
            date_check_out_to = current_or_previous[0]._get_datetime_from_field(
                dt_utc_without_tz, "hour_check_out_to"
            )
            if dt_utc_without_tz < date_check_out_from:
                return "CHECK-OUT-EARLIER", current_or_previous[0]
            elif date_check_out_from <= dt_utc_without_tz <= date_check_out_to:
                return "CHECK-OUT-ONTIME", current_or_previous[0]
            else:
                return "CHECK-OUT-LATE", current_or_previous[0]
        else:
            return "CHECK-OUT-NO-PREVIOUS", self.env["resource.calendar.attendance"]

    def _post_checkout_process_attendance(self, attendances, attendance):
        """Process a completed attendance record after check-out to calculate
        overtime by potentially splitting the attendance into separate regular
        and overtime records based on theoretical work schedules.

        :param attendances: The accumulated recordset of processed attendances.
        :type attendances: hr.attendance
        :param attendance: The attendance record just checked out.
        :type attendance: hr.attendance
        :return: The updated recordset including newly created or modified attendances.
        :rtype: hr.attendance
        """
        HrAttendance = self.env["hr.attendance"]
        attendances += attendance
        check_in_code, worktime = self._get_check_in_reason_code(attendance.check_in)
        attendance._add_reason_by_code(check_in_code)
        if check_in_code == "CHECK-IN-EARLIER":
            check_in_from_dt = worktime._get_datetime_from_field(
                attendance.check_in, "hour_check_in_from"
            )
            if attendance.check_out > check_in_from_dt:
                check_out = attendance.check_out
                attendance.check_out = check_in_from_dt
                attendances = self._post_checkout_process_attendance(
                    attendances,
                    HrAttendance.with_user(SUPERUSER_ID).create(
                        {
                            "employee_id": self.id,
                            "check_in": check_in_from_dt,
                            "check_out": check_out,
                            "is_overtime": False,
                        }
                    ),
                )
        if check_in_code in ["CHECK-IN-ONTIME", "CHECK-IN-LATE"]:
            check_out_to_dt = worktime._get_datetime_from_field(
                attendance.check_in, "hour_check_out_to"
            )
            if attendance.check_out > check_out_to_dt:
                check_out = attendance.check_out
                attendance.check_out = check_out_to_dt
                attendances = self._post_checkout_process_attendance(
                    attendances,
                    HrAttendance.with_user(SUPERUSER_ID).create(
                        {
                            "employee_id": self.id,
                            "check_in": check_out_to_dt,
                            "check_out": check_out,
                            "is_overtime": True,
                        }
                    ),
                )

        if check_in_code in ["CHECK-IN-EARLIER", "CHECK-IN-NO-NEXT"]:
            attendance.is_overtime = True

        check_out_code, worktime = self._get_check_out_reason_code(attendance.check_out)
        attendance._add_reason_by_code(check_out_code)
        if check_out_code in [
            "CHECK-OUT-NO-PREVIOUS",
        ]:
            attendance.is_overtime = True
        return attendances

    def _attendance_action_change(self, geo_information=None):
        """Improve hr_attendance Check In/Check Out action by handling overtime
        processing upon check-out.

        :param geo_information: Optional geographic coordinates of the check-in/out.
        :type geo_information: dict
        :return: A recordset of the modified or created `hr.attendance` records.
        :rtype: hr.attendance
        """
        attendance = super()._attendance_action_change(geo_information=geo_information)
        attendances = self.env["hr.attendance"].browse()
        if attendance.check_out:
            attendances = self._post_checkout_process_attendance(
                attendances, attendance
            )
        else:
            attendances += attendance
        return attendances
