# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from datetime import datetime

from freezegun import freeze_time
from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestHrAttendanceOverTime(TransactionCase):
    def setUp(self):
        super().setUp()
        self.HrAttendance = self.env["hr.attendance"]
        employee_group = self.env.ref("hr_attendance.group_hr_attendance_user")
        self.user_employee = self.env["res.users"].create(
            {
                "name": "Test User Employee",
                "login": "test2",
                "email": "test2@test.com",
                "groups_id": [(4, employee_group.id)],
                "tz": "UTC",
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee",
                "tz": "UTC",
                "user_id": self.user_employee.id,
            }
        )

        self.ci_earlier = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_in_earlier"
        )
        self.ci_late = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_in_late"
        )
        self.co_earlier = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_out_earlier"
        )
        self.co_late = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_out_late"
        )
        self.no_next = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_in_no_next"
        )
        self.no_previous = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_out_no_previous"
        )
        self.auto_close = self.env.ref(
            "hr_attendance_autoclose.hr_attendance_reason_check_out"
        )

        self.calendar = self.employee.resource_calendar_id
        # ensure monday morning configuration
        self.calendar.tz = "UTC"
        self.monday_morning = self.calendar.attendance_ids[0]
        monday_afternoon = self.calendar.attendance_ids[1]
        self.monday_morning.hour_check_in_from = 8 - 15 / 60
        self.monday_morning.hour_from = 8
        self.monday_morning.hour_check_in_to = 8 + 5 / 60
        self.monday_morning.hour_check_out_from = 10 - 5 / 60
        self.monday_morning.hour_to = 10
        self.monday_morning.hour_check_out_to = 10 + 5 / 60

        self.monday_morning.copy(
            default={
                "hour_check_in_from": 11 - 5 / 60,
                "hour_from": 11,
                "hour_check_in_to": 11 + 5 / 60,
                "hour_check_out_from": 12 - 5 / 60,
                "hour_to": 12,
                "hour_check_out_to": 12 + 5 / 60,
            }
        )
        monday_afternoon.hour_check_in_from = 13 - 5 / 60
        monday_afternoon.hour_from = 13
        monday_afternoon.hour_check_in_to = 13 + 5 / 60
        monday_afternoon.hour_check_out_from = 17 - 5 / 60
        monday_afternoon.hour_to = 17
        monday_afternoon.hour_check_out_to = 17 + 5 / 60
        self.employee = self.employee.with_user(self.user_employee)

    def test_todays_working_times(self):
        self.maxDiff = None
        with freeze_time("2021-12-13 06:01", tz_offset=0):
            self.employee._attendance_action_change()
        with freeze_time("2021-12-13 12:01", tz_offset=0):
            self.employee._attendance_action_change()
        with freeze_time("2021-12-13 14:11", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 19:01", tz_offset=0):
            self.assertEqual(
                self.employee.todays_working_times([("id", "=", self.employee.id)]),
                {
                    "done_attendances": [
                        {
                            "start": datetime(2021, 12, 13, 0, 0),
                            "end": datetime(2021, 12, 13, 6, 1),
                            "hours": 6.016666666666667,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 6, 1),
                            "end": datetime(2021, 12, 13, 7, 45),
                            "hours": 1.7333333333333334,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 7, 45),
                            "end": datetime(2021, 12, 13, 10, 5),
                            "hours": 2.3333333333333335,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 10, 5),
                            "end": datetime(2021, 12, 13, 10, 55),
                            "hours": 0.8333333333333334,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 10, 55),
                            "end": datetime(2021, 12, 13, 12, 1),
                            "hours": 1.1,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 12, 1),
                            "end": datetime(2021, 12, 13, 14, 11),
                            "hours": 2.1666666666666665,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 14, 11),
                            "end": datetime(2021, 12, 13, 19, 1),
                            "hours": 4.833333333333333,
                            "is_checked_out": False,
                            "is_worktime": True,
                        },
                    ],
                    "message": "Have a good break, thaks for your time",
                    "state": "CHECK-OUT-LATE",
                    "theoretical_work_times": [
                        {
                            "start": datetime(2021, 12, 13, 0, 0),
                            "end": datetime(2021, 12, 13, 7, 45),
                            "hours": 7.75,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 7, 45),
                            "end": datetime(2021, 12, 13, 10, 5),
                            "hours": 2.3333333333333335,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 10, 5),
                            "end": datetime(2021, 12, 13, 10, 55),
                            "hours": 0.8333333333333334,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 10, 55),
                            "end": datetime(2021, 12, 13, 12, 5),
                            "hours": 1.1666666666666667,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 12, 5),
                            "end": datetime(2021, 12, 13, 12, 55),
                            "hours": 0.8333333333333334,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 12, 55),
                            "end": datetime(2021, 12, 13, 17, 5),
                            "hours": 4.166666666666667,
                            "is_worktime": True,
                        },
                    ],
                },
            )

    @mute_logger("odoo.sql_db")
    def test_check_in_from_is_lower_than_check_in_to(self):
        self.monday_morning.hour_check_in_to = 2
        with self.assertRaisesRegex(
            IntegrityError, ".*c-in_from_is_lower_than_c-in_to"
        ):
            self.monday_morning.flush()

    @mute_logger("odoo.sql_db")
    def test_check_out_from_is_lower_than_check_out_to(self):
        self.monday_morning.hour_check_out_to = 2
        with self.assertRaisesRegex(
            IntegrityError, ".*c-out_from_is_lower_than_c-out_to"
        ):
            self.monday_morning.flush()

    @mute_logger("odoo.sql_db")
    def test_check_in_to_is_lower_than_check_out_from(self):
        self.monday_morning.hour_check_out_from = 2
        with self.assertRaisesRegex(
            IntegrityError, ".*c-in_to_is_lower_than_c-out_from"
        ):
            self.monday_morning.flush()

    def test_onchange_monday_morning_line(self):
        parameterized = [
            ("hour_check_in_from", -1, self.monday_morning._onchange_check_in_hours, 0),
            ("hour_check_in_to", -1, self.monday_morning._onchange_check_in_hours, 0),
            (
                "hour_check_in_from",
                25,
                self.monday_morning._onchange_check_in_hours,
                23.99,
            ),
            (
                "hour_check_in_to",
                # check-in to is set to max check in from
                # set to 23.99 in previous round trip
                3,
                self.monday_morning._onchange_check_in_hours,
                23.99,
            ),
            (
                "hour_check_out_from",
                -1,
                self.monday_morning._onchange_check_out_hours,
                0,
            ),
            ("hour_check_out_to", -1, self.monday_morning._onchange_check_out_hours, 0),
            (
                "hour_check_out_from",
                25,
                self.monday_morning._onchange_check_out_hours,
                23.99,
            ),
            (
                "hour_check_out_to",
                24,
                self.monday_morning._onchange_check_out_hours,
                23.99,
            ),
        ]
        for i, element in enumerate(parameterized):
            field_name, set_value, method, expected_value = element
            setattr(self.monday_morning, field_name, set_value)
            method()
            self.assertEqual(
                getattr(self.monday_morning, field_name),
                expected_value,
                f"Expected number do not match testing the element indice {i}.",
            )

    def test_create_calendar_set_default_hours(self):
        cal = self.env["resource.calendar"].create({"name": "test"})
        self.assertTrue(cal.attendance_ids)
        for line in cal.attendance_ids:
            self.assertEqual(line.hour_from, line.hour_check_in_from)
            self.assertEqual(line.hour_from, line.hour_check_in_to)
            self.assertEqual(line.hour_to, line.hour_check_out_from)
            self.assertEqual(line.hour_to, line.hour_check_out_to)

    def test_no_ir_cron_after_ran_after_end_of_first_interval(self):
        with freeze_time("2021-12-13 06:01", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 6, 1))
            self.assertFalse(attendance.check_out)
            self.assertFalse(attendance.is_overtime)
            self.assertFalse(attendance.attendance_reason_ids)

        with freeze_time("2021-12-13 19:01", tz_offset=0):
            attendances = self.employee._attendance_action_change()
            attendances2 = self.HrAttendance.search(
                [("employee_id", "=", self.employee.id)]
            )
            self.assertEqual(len(attendances), 7)
            self.assertEqual(len(attendances2), 7)
            self.assertEqual(attendances[0].check_in, datetime(2021, 12, 13, 6, 1))
            self.assertEqual(attendances[0].check_out, datetime(2021, 12, 13, 7, 45))
            self.assertTrue(attendances[0].is_overtime)
            self.assertEqual(attendances[1].check_in, datetime(2021, 12, 13, 7, 45))
            self.assertEqual(attendances[1].check_out, datetime(2021, 12, 13, 10, 5))
            self.assertFalse(attendances[1].is_overtime)
            self.assertEqual(attendances[2].check_in, datetime(2021, 12, 13, 10, 5))
            self.assertEqual(attendances[2].check_out, datetime(2021, 12, 13, 10, 55))
            self.assertTrue(attendances[2].is_overtime)
            self.assertEqual(attendances[3].check_in, datetime(2021, 12, 13, 10, 55))
            self.assertEqual(attendances[3].check_out, datetime(2021, 12, 13, 12, 5))
            self.assertFalse(attendances[3].is_overtime)
            self.assertEqual(attendances[4].check_in, datetime(2021, 12, 13, 12, 5))
            self.assertEqual(attendances[4].check_out, datetime(2021, 12, 13, 12, 55))
            self.assertTrue(attendances[4].is_overtime)
            self.assertEqual(attendances[5].check_in, datetime(2021, 12, 13, 12, 55))
            self.assertEqual(attendances[5].check_out, datetime(2021, 12, 13, 17, 5))
            self.assertFalse(attendances[5].is_overtime)
            self.assertEqual(attendances[6].check_in, datetime(2021, 12, 13, 17, 5))
            self.assertEqual(attendances[6].check_out, datetime(2021, 12, 13, 19, 1))
            self.assertTrue(attendances[6].is_overtime)

    def test_checkin_before_create_overtime(self):
        with freeze_time("2021-12-13 07:44", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 10:01", tz_offset=0):
            attendances = self.employee._attendance_action_change()
            self.assertEqual(len(attendances), 2)
            self.assertEqual(attendances[0].check_in, datetime(2021, 12, 13, 7, 44))
            self.assertEqual(attendances[0].check_out, datetime(2021, 12, 13, 7, 45))
            self.assertTrue(attendances[0].is_overtime)
            self.assertTrue(self.ci_earlier in attendances[0].attendance_reason_ids)
            self.assertEqual(attendances[1].check_in, datetime(2021, 12, 13, 7, 45))
            self.assertEqual(attendances[1].check_out, datetime(2021, 12, 13, 10, 1))
            self.assertFalse(attendances[1].is_overtime)
            self.assertFalse(attendances[1].attendance_reason_ids)

    def test_checkin_and_checkout_before_futures_wortime(self):
        with freeze_time("2021-12-13 06:45", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 06:55", tz_offset=0):
            self.employee._attendance_action_change()
        attendances = self.HrAttendance.search([("employee_id", "=", self.employee.id)])
        attendances.ensure_one()
        self.assertEqual(attendances.check_in, datetime(2021, 12, 13, 6, 45))
        self.assertEqual(attendances.check_out, datetime(2021, 12, 13, 6, 55))
        self.assertTrue(attendances.is_overtime)
        self.assertTrue(self.ci_earlier in attendances[0].attendance_reason_ids)

    def test_check_in_out_on_time(self):
        with freeze_time("2021-12-13 08:01", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 10:01", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 8, 1))
            self.assertEqual(attendance.check_out, datetime(2021, 12, 13, 10, 1))
            self.assertFalse(attendance.is_overtime)
            self.assertFalse(attendance.attendance_reason_ids)

    def test_checkin_late(self):
        with freeze_time("2021-12-13 08:16", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 10:01", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 8, 16))
            self.assertEqual(attendance.check_out, datetime(2021, 12, 13, 10, 1))
            self.assertFalse(attendance.is_overtime)
            self.assertTrue(self.ci_late in attendance.attendance_reason_ids)

    def test_checkout_earlier(self):
        with freeze_time("2021-12-13 08:00", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 09:30", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 8, 0))
            self.assertEqual(attendance.check_out, datetime(2021, 12, 13, 9, 30))
            self.assertFalse(attendance.is_overtime)
            self.assertTrue(self.co_earlier in attendance.attendance_reason_ids)

    def test_checkout_late(self):
        with freeze_time("2021-12-13 08:00", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 10:10", tz_offset=0):
            attendances = self.employee._attendance_action_change()
            self.assertEqual(len(attendances), 2)
            self.assertEqual(attendances[0].check_in, datetime(2021, 12, 13, 8, 0))
            self.assertEqual(attendances[0].check_out, datetime(2021, 12, 13, 10, 5))
            self.assertFalse(attendances[0].is_overtime)
            self.assertFalse(attendances[0].attendance_reason_ids)
            self.assertEqual(attendances[1].check_in, datetime(2021, 12, 13, 10, 5))
            self.assertEqual(attendances[1].check_out, datetime(2021, 12, 13, 10, 10))
            self.assertTrue(attendances[1].is_overtime)
            self.assertTrue(self.co_late in attendances[1].attendance_reason_ids)

    def test_checkin_earlier_checkout_later(self):
        with freeze_time("2021-12-13 10:45", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 12:10", tz_offset=0):
            attendances = self.employee._attendance_action_change()
            self.assertEqual(len(attendances), 3)

            self.assertEqual(attendances[0].check_in, datetime(2021, 12, 13, 10, 45))
            self.assertEqual(attendances[0].check_out, datetime(2021, 12, 13, 10, 55))
            self.assertTrue(attendances[0].is_overtime)
            self.assertTrue(self.ci_earlier in attendances[0].attendance_reason_ids)

            self.assertEqual(attendances[1].check_in, datetime(2021, 12, 13, 10, 55))
            self.assertEqual(attendances[1].check_out, datetime(2021, 12, 13, 12, 5))
            self.assertFalse(attendances[1].is_overtime)
            self.assertFalse(attendances[1].attendance_reason_ids)

            self.assertEqual(attendances[2].check_in, datetime(2021, 12, 13, 12, 5))
            self.assertEqual(attendances[2].check_out, datetime(2021, 12, 13, 12, 10))
            self.assertTrue(attendances[2].is_overtime)
            self.assertTrue(self.co_late in attendances[2].attendance_reason_ids)

    def test_weekend(self):
        with freeze_time("2021-12-12 10:45", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-12 12:10", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 12, 10, 45))
            self.assertEqual(attendance.check_out, datetime(2021, 12, 12, 12, 10))
            self.assertTrue(attendance.is_overtime)
            self.assertTrue(self.no_next in attendance.attendance_reason_ids)
            self.assertTrue(self.no_previous in attendance.attendance_reason_ids)

    def test_check_in_check_out_end_of_day(self):
        with freeze_time("2021-12-13 19:45", tz_offset=0):
            attendance = self.employee._attendance_action_change()

        with freeze_time("2021-12-13 20:10", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 19, 45))
            self.assertEqual(attendance.check_out, datetime(2021, 12, 13, 20, 10))
            self.assertTrue(attendance.is_overtime)
            self.assertTrue(self.no_next in attendance.attendance_reason_ids)
            self.assertTrue(self.no_previous not in attendance.attendance_reason_ids)

    def test_checkout_autoclose(self):
        with freeze_time("2021-12-13 08:01", tz_offset=0):
            attendance = self.employee._attendance_action_change()

        with freeze_time("2021-12-13 10:04", tz_offset=0):
            self.HrAttendance.check_for_incomplete_attendances()
            attendance = self.HrAttendance.search(
                [("employee_id", "=", self.employee.id)], order="check_in"
            )
            attendance.ensure_one()
            self.assertFalse(attendance.check_out)
            self.assertFalse(attendance.attendance_reason_ids)

        with freeze_time("2021-12-13 10:35", tz_offset=0):
            self.HrAttendance.check_for_incomplete_attendances()
            attendances = self.HrAttendance.search(
                [("employee_id", "=", self.employee.id)], order="check_in"
            )
            self.assertEqual(len(attendances), 2)
            self.assertEqual(attendances[0].check_in, datetime(2021, 12, 13, 8, 1))
            self.assertEqual(attendances[0].check_out, datetime(2021, 12, 13, 10, 5))
            self.assertFalse(attendances[0].is_overtime)
            attendances[0].attendance_reason_ids.ensure_one()
            self.assertTrue(self.auto_close in attendances[0].attendance_reason_ids)
            self.assertEqual(attendances[1].check_in, datetime(2021, 12, 13, 10, 5))
            self.assertEqual(attendances[1].check_out, datetime(2021, 12, 13, 10, 35))
            self.assertTrue(attendances[1].is_overtime)
            self.assertEqual(len(attendances[1].attendance_reason_ids), 3)
            self.assertTrue(self.auto_close in attendances[1].attendance_reason_ids)
            self.assertTrue(self.ci_earlier in attendances[1].attendance_reason_ids)
            self.assertTrue(self.co_late in attendances[1].attendance_reason_ids)

    def test_checkin_in_late_autoclose_use_autoclose_rule(self):
        self.env.company.attendance_maximum_hours_per_day = 1
        with freeze_time("2021-12-13 19:50", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 21:05", tz_offset=0):
            self.HrAttendance.check_for_incomplete_attendances()
            attendance = self.HrAttendance.search(
                [("employee_id", "=", self.employee.id)], order="check_in"
            )
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 19, 50))
            self.assertEqual(attendance.check_out, datetime(2021, 12, 13, 20, 50))
            self.assertEqual(len(attendance.attendance_reason_ids), 1)
            self.assertTrue(self.auto_close in attendance.attendance_reason_ids)
            self.assertTrue(attendance.is_overtime)

    def test_autoclose_all_day(self):
        self.env.company.attendance_maximum_hours_per_day = 1
        with freeze_time("2021-12-13 06:38", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 21:05", tz_offset=0):
            self.HrAttendance.check_for_incomplete_attendances()
            attendances = self.HrAttendance.search(
                [("employee_id", "=", self.employee.id)], order="check_in"
            )
            self.assertEqual(len(attendances), 7)


class TestHrAttendanceOverTimeEuropeParis(TransactionCase):
    def setUp(self):
        super().setUp()
        self.HrAttendance = self.env["hr.attendance"]
        employee_group = self.env.ref("hr_attendance.group_hr_attendance_user")
        self.user_employee = self.env["res.users"].create(
            {
                "name": "Test User Employee",
                "login": "test2",
                "email": "test2@test.com",
                "groups_id": [(4, employee_group.id)],
                "tz": "Europe/Paris",
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee",
                "tz": "Europe/Paris",
                "user_id": self.user_employee.id,
            }
        )

        self.ci_earlier = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_in_earlier"
        )
        self.ci_late = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_in_late"
        )
        self.co_earlier = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_out_earlier"
        )
        self.co_late = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_out_late"
        )
        self.no_next = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_in_no_next"
        )
        self.no_previous = self.env.ref(
            "hr_attendance_overtime.hr_attendance_reason_check_out_no_previous"
        )
        self.auto_close = self.env.ref(
            "hr_attendance_autoclose.hr_attendance_reason_check_out"
        )

        self.calendar = self.employee.resource_calendar_id
        # ensure monday morning configuration
        self.calendar.tz = "Europe/Paris"
        self.monday_morning = self.calendar.attendance_ids[0]
        monday_afternoon = self.calendar.attendance_ids[1]
        self.monday_morning.hour_check_in_from = 8 - 15 / 60
        self.monday_morning.hour_from = 8
        self.monday_morning.hour_check_in_to = 8 + 5 / 60
        self.monday_morning.hour_check_out_from = 10 - 5 / 60
        self.monday_morning.hour_to = 10
        self.monday_morning.hour_check_out_to = 10 + 5 / 60

        self.monday_morning.copy(
            default={
                "hour_check_in_from": 11 - 5 / 60,
                "hour_from": 11,
                "hour_check_in_to": 11 + 5 / 60,
                "hour_check_out_from": 12 - 5 / 60,
                "hour_to": 12,
                "hour_check_out_to": 12 + 5 / 60,
            }
        )
        monday_afternoon.hour_check_in_from = 13 - 5 / 60
        monday_afternoon.hour_from = 13
        monday_afternoon.hour_check_in_to = 13 + 5 / 60
        monday_afternoon.hour_check_out_from = 17 - 5 / 60
        monday_afternoon.hour_to = 17
        monday_afternoon.hour_check_out_to = 17 + 5 / 60
        self.employee = self.employee.with_user(self.user_employee)

    def test_checkin_before_create_overtime(self):
        with freeze_time("2021-12-13 06:44", tz_offset=0):
            attendances = self.employee._attendance_action_change()
            attendances.ensure_one()

        with freeze_time("2021-12-13 09:01", tz_offset=0):
            attendances = self.employee._attendance_action_change()
            self.assertEqual(len(attendances), 2)
            # data are saved and manipulated in utc time
            self.assertEqual(attendances[0].check_in, datetime(2021, 12, 13, 6, 44))
            self.assertEqual(attendances[0].check_out, datetime(2021, 12, 13, 6, 45))
            self.assertTrue(attendances[0].is_overtime)
            self.assertTrue(self.ci_earlier in attendances[0].attendance_reason_ids)
            self.assertEqual(attendances[1].check_in, datetime(2021, 12, 13, 6, 45))
            self.assertEqual(attendances[1].check_out, datetime(2021, 12, 13, 9, 1))
            self.assertFalse(attendances[1].is_overtime)
            self.assertFalse(attendances[1].attendance_reason_ids)

    def test_check_in_on_out_time(self):
        with freeze_time("2021-12-13 07:01", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 7, 1))
            self.assertFalse(attendance.check_out)
            self.assertFalse(attendance.is_overtime)
            self.assertFalse(attendance.attendance_reason_ids)

        with freeze_time("2021-12-13 09:01", tz_offset=0):
            attendance = self.employee._attendance_action_change()
            attendance.ensure_one()
            self.assertEqual(attendance.check_in, datetime(2021, 12, 13, 7, 1))
            self.assertEqual(attendance.check_out, datetime(2021, 12, 13, 9, 1))
            self.assertFalse(attendance.is_overtime)
            self.assertFalse(attendance.attendance_reason_ids)

    def test_todays_working_times(self):
        self.maxDiff = None
        with freeze_time("2021-12-13 05:01", tz_offset=0):
            self.employee._attendance_action_change()

        with freeze_time("2021-12-13 18:01", tz_offset=0):
            self.employee._attendance_action_change()
            self.assertEqual(
                self.employee.todays_working_times([("id", "=", self.employee.id)]),
                {
                    "done_attendances": [
                        {
                            "start": datetime(2021, 12, 12, 23, 0),
                            "end": datetime(2021, 12, 13, 5, 1),
                            "hours": 6.016666666666667,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 5, 1),
                            "end": datetime(2021, 12, 13, 6, 45),
                            "hours": 1.7333333333333334,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 6, 45),
                            "end": datetime(2021, 12, 13, 9, 5),
                            "hours": 2.3333333333333335,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 9, 5),
                            "end": datetime(2021, 12, 13, 9, 55),
                            "hours": 0.8333333333333334,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 9, 55),
                            "end": datetime(2021, 12, 13, 11, 5),
                            "hours": 1.1666666666666667,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 11, 5),
                            "end": datetime(2021, 12, 13, 11, 55),
                            "hours": 0.8333333333333334,
                            "is_worktime": True,
                            "is_checked_out": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 11, 55),
                            "end": datetime(2021, 12, 13, 16, 5),
                            "hours": 4.166666666666667,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 16, 5),
                            "end": datetime(2021, 12, 13, 18, 1),
                            "hours": 1.9333333333333333,
                            "is_checked_out": True,
                            "is_worktime": True,
                        },
                    ],
                    "message": "You shouldn't start working at that time...",
                    "state": "CHECK-IN-NO-NEXT",
                    "theoretical_work_times": [
                        {
                            "start": datetime(2021, 12, 12, 23, 0),
                            "end": datetime(2021, 12, 13, 6, 45),
                            "hours": 7.75,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 6, 45),
                            "end": datetime(2021, 12, 13, 9, 5),
                            "hours": 2.3333333333333335,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 9, 5),
                            "end": datetime(2021, 12, 13, 9, 55),
                            "hours": 0.8333333333333334,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 9, 55),
                            "end": datetime(2021, 12, 13, 11, 5),
                            "hours": 1.1666666666666667,
                            "is_worktime": True,
                        },
                        {
                            "start": datetime(2021, 12, 13, 11, 5),
                            "end": datetime(2021, 12, 13, 11, 55),
                            "hours": 0.8333333333333334,
                            "is_worktime": False,
                        },
                        {
                            "start": datetime(2021, 12, 13, 11, 55),
                            "end": datetime(2021, 12, 13, 16, 5),
                            "hours": 4.166666666666667,
                            "is_worktime": True,
                        },
                    ],
                },
            )
