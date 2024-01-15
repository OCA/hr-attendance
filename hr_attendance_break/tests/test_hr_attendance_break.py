# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


import datetime
import time
from unittest.mock import patch

from odoo import exceptions
from odoo.tests.common import TransactionCase

from ..models.hr_employee import fields as hr_employee_fields


class TestHrAttendance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["hr.attendance"].search([]).unlink()
        cls.employee = cls.env.ref("hr.employee_admin")
        cls.attendance = cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee.id,
                "check_in": datetime.datetime(2023, 8, 21, 7, 0, 0),
                "check_out": datetime.datetime(2023, 8, 21, 17, 0, 0),
                "break_ids": [
                    (0, 0, {"begin": datetime.datetime(2023, 8, 21, 7, 30, 0)}),
                ],
            }
        )

    def test_break_computation(self):
        """Test that computing breaks from an attendance works"""
        self.assertEqual(self.employee.break_state, "on_break")
        self.assertEqual(self.attendance.worked_hours, 10)
        self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 8, 0, 0)
        self.assertEqual(self.employee.break_state, "no_break")
        self.assertEqual(self.attendance.break_hours, 0.5)
        self.assertEqual(self.attendance.worked_hours, 9.5)
        with patch.object(
            hr_employee_fields.Datetime,
            "now",
            side_effect=lambda: datetime.datetime(2023, 8, 21, 18, 0, 0),
        ):
            self.assertEqual(self.employee.break_hours_today, 0.5)

    def test_mandatory_break(self):
        """Test that we flag for minimal break taken"""
        original_activities = self.employee.activity_ids
        # no break, should flag and impose break
        self.employee._check_mandatory_break(datetime.datetime(2023, 8, 21))
        flag_activity = self.employee.activity_ids - original_activities
        self.assertEqual(
            flag_activity.activity_type_id,
            self.env.ref("hr_attendance_break.activity_type_mandatory_break"),
        )
        original_activities += flag_activity
        self.assertEqual(len(self.attendance.break_ids), 2)
        imposed_break = self.attendance.break_ids.filtered(
            lambda x: x.reason_id == self.env.ref("hr_attendance_break.reason_imposed")
        )
        self.assertEqual(imposed_break.break_hours, 0.75)
        # break is exactly minimum, no flag
        imposed_break.unlink()
        self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 8, 15, 0)
        self.employee._check_mandatory_break(datetime.datetime(2023, 8, 21))
        flag_activity = self.employee.activity_ids - original_activities
        self.assertFalse(flag_activity)
        # break is a little bit less than minimum, flag and impose break
        self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 8, 13, 0)
        self.employee._check_mandatory_break(datetime.datetime(2023, 8, 21))
        flag_activity = self.employee.activity_ids - original_activities
        self.assertTrue(flag_activity)
        original_activities += flag_activity
        imposed_break = self.attendance.break_ids.filtered(
            lambda x: x.reason_id == self.env.ref("hr_attendance_break.reason_imposed")
        )
        self.assertEqual(imposed_break.break_hours, 1 / 30)
        self.assertEqual(sum(self.attendance.break_ids.mapped("break_hours")), 0.75)
        # break is not actually a break but just two attendances with time in between
        # that suffices for this day as mandatory break
        self.attendance.break_ids.unlink()
        self.attendance.check_out = datetime.datetime(2023, 8, 21, 11, 0, 0)
        self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime.datetime(2023, 8, 21, 13, 0, 0),
                "check_out": datetime.datetime(2023, 8, 21, 17, 0, 0),
            }
        )
        with patch.object(
            hr_employee_fields.Date,
            "context_today",
            side_effect=lambda record: datetime.datetime(2023, 8, 22),
        ):
            self.employee._check_mandatory_break_yesterday()
        flag_activity = self.employee.activity_ids - original_activities
        self.assertFalse(flag_activity)

    def test_manual_break(self):
        """Test break taking works as expected"""
        self.employee.invalidate_cache(["hr_presence_state", "break_state"])
        attendance = self.employee._attendance_action_change()
        self.assertFalse(attendance.break_ids)
        self.assertEqual(self.employee.hr_presence_state, "present")
        self.employee.attendance_manual_break(None)
        self.assertTrue(attendance.break_ids)
        self.assertEqual(self.employee.hr_presence_state, "absent")
        # begin is datetime.now(), but below the code will set
        # end to datetime.now() which will fail the constraint begin<end
        time.sleep(1)
        self.employee.attendance_manual_break(None)
        self.assertTrue(attendance.break_ids.end)
        self.assertEqual(self.employee.hr_presence_state, "present")

    def test_buttons(self):
        """Test our button handlers"""
        config_settings = self.env["res.config.settings"].create({})
        action = config_settings.button_hr_attendance_break_thresholds()
        self.assertEqual(
            self.env["hr.attendance.break.threshold"].search(action["domain"]),
            self.employee.company_id.hr_attendance_break_threshold_ids,
        )
        action = config_settings.button_hr_attendance_break_action()
        self.assertEqual(
            action["res_id"],
            self.env.ref("hr_attendance_break.action_mandatory_break").id,
        )
        action = self.attendance.button_show_breaks()
        self.assertEqual(
            self.env["hr.attendance.break"].search(action["domain"]),
            self.attendance.break_ids,
        )

    def test_overtime(self):
        """Test that breaks decrease overtime"""

        def get_overtime(attendance):
            _dummy, date = attendance._get_day_start_and_day(
                attendance.employee_id, attendance.check_in
            )
            return self.env["hr.attendance.overtime"].search(
                [
                    ("employee_id", "=", self.employee.id),
                    ("date", "=", date),
                ]
            )

        self.employee.company_id.write(
            {
                "hr_attendance_overtime": True,
                "overtime_start_date": datetime.date(2023, 8, 20),
                "overtime_company_threshold": 0,
                "overtime_employee_threshold": 0,
            }
        )

        # should work 8, has worked 10
        self.assertEqual(get_overtime(self.attendance).duration, 2)
        self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 8, 30, 0)
        self.assertEqual(get_overtime(self.attendance).duration, 1)
        self.attendance.break_ids.unlink()
        self.assertEqual(get_overtime(self.attendance).duration, 2)
        no_work_attendance = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime.datetime(2023, 8, 26, 7, 0, 0),
                "check_out": datetime.datetime(2023, 8, 26, 17, 0, 0),
            }
        )
        self.assertEqual(get_overtime(no_work_attendance).duration, 10)
        no_work_attendance.write(
            {
                "break_ids": [
                    (
                        0,
                        0,
                        {
                            "begin": datetime.datetime(2023, 8, 26, 7, 30, 0),
                            "end": datetime.datetime(2023, 8, 26, 8, 0, 0),
                        },
                    ),
                ],
            }
        )
        self.assertEqual(get_overtime(no_work_attendance).duration, 9.5)
        exact_worktime_attendance = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime.datetime(2023, 8, 28, 7, 0, 0),
                "check_out": datetime.datetime(2023, 8, 28, 15, 0, 0),
                "break_ids": [
                    (
                        0,
                        0,
                        {
                            "begin": datetime.datetime(2023, 8, 28, 7, 30, 0),
                            "end": datetime.datetime(2023, 8, 28, 8, 0, 0),
                        },
                    ),
                ],
            }
        )
        self.assertEqual(get_overtime(exact_worktime_attendance).duration, -0.5)

    def test_overlap(self):
        """Test we can't have overlapping breaks"""
        with self.assertRaises(exceptions.ValidationError):
            self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 17, 1)
        self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 17, 0, 0)
        with self.assertRaises(exceptions.ValidationError):
            self.attendance.check_out = datetime.datetime(2023, 8, 21, 16, 59, 0)
        self.attendance.break_ids.end = datetime.datetime(2023, 8, 21, 8, 0, 0)
        self.env["hr.attendance.break"].create(
            {
                "attendance_id": self.attendance.id,
                "begin": datetime.datetime(2023, 8, 21, 8, 0, 0),
                "end": datetime.datetime(2023, 8, 21, 8, 30, 0),
            }
        )
        with self.assertRaises(exceptions.ValidationError), self.env.cr.savepoint():
            self.attendance.break_ids[0].end = datetime.datetime(2023, 8, 21, 8, 1)
        # but be sure that breaks of different users may overlap
        attendance_demo_user = self.attendance.create(
            self.attendance.copy_data(
                default={"employee_id": self.env.ref("hr.employee_qdp").id}
            )
        )
        self.env["hr.attendance.break"].create(
            {
                "attendance_id": attendance_demo_user.id,
                "begin": datetime.datetime(2023, 8, 21, 8, 0, 0),
                "end": datetime.datetime(2023, 8, 21, 8, 30, 0),
            }
        )
