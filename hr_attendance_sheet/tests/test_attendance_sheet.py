# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase, new_test_user


@freeze_time("2023-02-01")
class TestAttendanceSheet(TransactionCase):
    def setUp(self):
        super().setUp()
        self.AttendanceSheet = self.env["hr.attendance.sheet"]
        self.ctx_new_test_user = {
            "mail_create_nolog": True,
            "mail_create_nosubscribe": True,
            "mail_notrack": True,
            "no_reset_password": True,
        }
        self.test_user_manager = new_test_user(
            self.env,
            login="test@test.com",
            groups="hr_attendance.group_hr_attendance_manager",
            context=self.ctx_new_test_user,
        )
        self.test_user_employee = new_test_user(
            self.env,
            login="test2@test.com",
            groups="hr_attendance.group_hr_attendance_user",
            context=self.ctx_new_test_user,
        )
        self.test_user_employee1 = new_test_user(
            self.env,
            login="test3@test.com",
            groups="hr_attendance.group_hr_attendance_user",
            context=self.ctx_new_test_user,
        )
        self.test_user_employee2 = new_test_user(
            self.env,
            login="test4@test.com",
            groups="hr_attendance.group_hr_attendance_user",
            context=self.ctx_new_test_user,
        )
        self.test_manager = self.env["hr.employee"].create(
            {
                "name": "TestManager",
                "user_id": self.test_user_manager.id,
                "use_attendance_sheets": True,
            }
        )
        self.test_employee = self.env["hr.employee"].create(
            {
                "name": "TestEmployee",
                "user_id": self.test_user_employee.id,
                "parent_id": self.test_manager.id,
                "use_attendance_sheets": True,
            }
        )
        self.test_employee1 = self.env["hr.employee"].create(
            {
                "name": "TestEmployee1",
                "user_id": self.test_user_employee2.id,
                "parent_id": self.test_manager.id,
                "use_attendance_sheets": True,
            }
        )
        self.test_attendance1 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-10 08:00",
                "check_out": "2023-01-10 12:00",
            }
        )
        self.test_attendance2 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-05 13:00",
                "check_out": "2023-01-05 17:00",
            }
        )

    def test_attendance_sheet(self):
        company = self.env.company
        company.write(
            {
                "use_attendance_sheets": True,
                "date_start": "2023-02-01",
                "attendance_sheet_range": "WEEKLY",
                "auto_lunch": True,
                "auto_lunch_duration": 0.5,
                "auto_lunch_hours": 0.5,
            }
        )

        # TEST01: Test create sheet method
        view_id = "hr_attendance_sheet.hr_attendance_sheet_view_form"
        with Form(self.AttendanceSheet, view=view_id) as f:
            f.employee_id = self.test_employee
            f.date_start = "2023-01-01"
            f.date_end = "2023-01-15"
        sheet = f.save()
        sheet.attendance_action_change()
        time.sleep(2)
        no_check_out_attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", self.test_employee.id),
                ("check_out", "=", False),
                ("id", "in", sheet.attendance_ids.ids),
            ],
            order="check_in desc",
        )
        for attend in no_check_out_attendances:
            attend.check_out = fields.Datetime.now()
        sheet.attendance_action_change()
        time.sleep(2)
        self.assertEqual(len(sheet.attendance_ids), 2)

        # # TEST02: Test new attendance linked to sheet
        self.test_attendance3 = sheet.attendance_ids[1]

        sheet.flush()
        self.assertEqual(len(sheet.attendance_ids), 2)

        # TEST03: Test sheet confirm with incorrect attendances
        no_check_out_attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", self.test_employee.id),
                ("check_out", "=", False),
                ("id", "in", sheet.attendance_ids.ids),
            ],
            order="check_in desc",
        )
        for attend in no_check_out_attendances:
            attend.check_out = fields.Datetime.now()
        self.test_attendance_inprogress = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-10 22:00",
            }
        )
        # sheet.action_attendance_sheet_confirm()
        self.test_attendance_inprogress.unlink()

        # TEST04: Test sheet confirm
        ids_not_checkout = sheet.attendance_ids.filtered(
            lambda att: att.check_in and not att.check_out
        )
        if ids_not_checkout:
            ids_not_checkout.check_out = fields.Datetime.now()
        sheet.action_attendance_sheet_confirm()
        sheet.state = "confirm"
        self.assertEqual(sheet.state, "confirm")

        # TEST05: Test sheet draft error when in confirm
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_manager).action_attendance_sheet_draft()

        # TEST06: Test sheet lock error when not approved
        with self.assertRaises(UserError):
            sheet.action_attendance_sheet_lock()

        # TEST07: Test sheet done (Not Reviewer)
        with self.assertRaises(UserError):
            sheet.action_attendance_sheet_done()

        # TEST08: Test sheet done with open attendance error
        attendance_ids = self.env["hr.attendance"].search(
            [("employee_id", "=", self.test_employee.id), ("check_out", "=", False)]
        )
        attendance_ids.write({"check_out": "2023-01-10 08:00"})
        attendance_ids.flush()
        self.test_attendance_open = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-12 08:00",
            }
        )
        sheet.with_user(self.test_user_manager).action_attendance_sheet_done()
        # self.test_attendance_open.unlink()

        # TEST09: Test sheet done (As Reviewer)
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_manager).action_attendance_sheet_done()

        # TEST10: Test sheet lock
        sheet.with_user(self.test_user_manager).action_attendance_sheet_lock()
        self.assertEqual(sheet.state, "locked")

        # TEST11: Test write sheet when locked
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_employee).write({"date_start": "2023-02-01"})

        # TEST12: Test error trying to write attendance
        with self.assertRaises(UserError):
            self.test_attendance3.write({"check_out": "2023-01-10 20:00"})

        # TEST13: Test error trying to delete attendance
        with self.assertRaises(UserError):
            self.test_attendance3.unlink()

        # TEST14: Test sheet unlock
        sheet.with_user(self.test_user_manager).action_attendance_sheet_unlock()
        self.assertEqual(sheet.state, "done")

        # TEST15: Test sheet draft
        sheet.with_user(self.test_user_manager).action_attendance_sheet_draft()
        self.assertEqual(sheet.state, "draft")

        # TEST16: Test sheet done error when in draft
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_manager).action_attendance_sheet_done()

        # TEST17: Test delete attendance
        self.test_attendance3.unlink()
        self.assertEqual(len(sheet.attendance_ids), 2)

        # TEST18: Test sheet refuse
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_manager).action_attendance_sheet_refuse()
        # sheet.with_user(self.test_user_employee).action_attendance_sheet_confirm()
        # sheet.with_user(self.test_user_manager).action_attendance_sheet_refuse()
        self.assertEqual(sheet.state, "draft")

        # TEST19: Set company date range to bi-weekly
        company.write({"attendance_sheet_range": "BIWEEKLY"})
        self.assertFalse(company.date_end)

        # TEST20: Test autolunch on attendance
        # clock_date = fields.Date.today() + timedelta(days=2)
        # with self.assertRaises(UserError):
        #     self.test_attendance4 = self.env["hr.attendance"].create(
        #         {
        #             "employee_id": self.test_employee1.id,
        #             "check_out": clock_date.strftime("%Y-%m-11 16:00"),
        #         }
        #     )
        #     self.assertEqual(self.test_attendance4.auto_lunch, False)

    def test_company_create_sheet_id(self):
        company = self.env.company
        company.write({"use_attendance_sheets": True})

        # TEST21: Scheduled Action No Company Start/End Date Error
        with self.assertRaises(UserError):
            self.AttendanceSheet._create_sheet_id()
        # TEST22: Company Start/End Date onchange
        company = self.env.company

        company.write(
            {
                "attendance_sheet_range": "WEEKLY",
                "attendance_sheet_review_policy": "employee_manager",
                "date_start": "2023-02-01",
                "date_end": "2023-02-15",
            }
        )
        company.onchange_attendance_sheet_range()
        self.assertEqual(company.date_start, fields.Date.from_string("2023-02-01"))

        # TEST23: Create Sheets Cron Method
        #        self.AttendanceSheet._create_sheet_id()
        #        sheets = self.env["hr.attendance.sheet"].search([])
        #        self.assertEqual(len(sheets), 2)

        # TEST24: Test _get_possible_reviewers for employee_manager
        sheet = self.env["hr.attendance.sheet"].search([], limit=1)
        self.assertEqual(len(sheet._get_possible_reviewers()), 1)

        # TEST25: Test _get_possible_reviewers for hr_or_manager
        company.write({"attendance_sheet_review_policy": "hr_or_manager"})
        sheet = self.env["hr.attendance.sheet"].search([], limit=1)
        self.assertEqual(len(sheet._get_possible_reviewers()), 1)

        # TEST26: Test confirm button with hr_or_manager policy
        sheet = self.env["hr.attendance.sheet"].search([], limit=1)
        sheet.with_user(self.test_user_employee1).action_attendance_sheet_confirm()
        self.assertFalse(sheet.state)

    def test_company_create(self):
        # TEST27: Create Company
        company = self.test_company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "date_start": "2023-02-01",
                "attendance_sheet_range": "BIWEEKLY",
            }
        )
        self.assertEqual(company.date_end, fields.Date.from_string("2023-02-14"))

    def test_company_start_end_date_change(self):
        # TEST28: Test changing start/end date on company via cron
        company = self.env.company
        company.write(
            {
                "date_start": "2023-01-25",
                "date_end": "2023-02-01",
                "use_attendance_sheets": True,
                "attendance_sheet_range": "WEEKLY",
                "attendance_sheet_review_policy": "employee_manager",
            }
        )
        self.AttendanceSheet._create_sheet_id()
        self.assertEqual(company.date_end, fields.Date.from_string("2023-02-01"))

    def test_set_date_end(self):
        # TEST29: Create Company and test else statement in set end date
        company = self.test_company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "date_start": "2023-02-01",
                "attendance_sheet_range": "DAILY",
            }
        )
        self.assertEqual(
            company.date_end,
            fields.Date.from_string("2023-02-28"),
        )

    def test_access_errors(self):
        self.test_user_basic = new_test_user(
            self.env,
            login="basic@test.com",
            groups="hr_attendance.group_hr_attendance",
            context=self.ctx_new_test_user,
        )
        self.test_basic_employee = self.env["hr.employee"].create(
            {
                "name": "TestBasicEmployee",
                "user_id": self.test_user_employee1.id,
                "parent_id": self.test_manager.id,
                "use_attendance_sheets": True,
            }
        )
        # self.test_basic_employee.flush()
        self.test_attendance1 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_basic_employee.id,
                "check_in": "2023-01-10 08:00",
                "check_out": "2023-01-10 12:00",
            }
        )
        # self.test_attendance1.flush()

        # Create sheet and confirm then done
        view_id = "hr_attendance_sheet.hr_attendance_sheet_view_form"
        with Form(self.AttendanceSheet, view=view_id) as f:
            f.employee_id = self.test_basic_employee
            f.date_start = "2023-02-01"
            f.date_end = "2023-02-15"
        sheet = f.save()
        sheet.action_attendance_sheet_confirm()

        # TEST30: errors based on policy
        company = self.env.company
        company.write({"attendance_sheet_review_policy": "hr"})
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_basic).action_attendance_sheet_refuse()
        company.write({"attendance_sheet_review_policy": "employee_manager"})
        # with self.assertRaises(UserError):
        #     sheet.with_user(self.test_user_basic).action_attendance_sheet_refuse()
        # company.write({"attendance_sheet_review_policy": "hr_or_manager"})
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_basic).action_attendance_sheet_refuse()

        # TEST31: error if basic employee tries to update approved sheet
        sheet.with_user(self.test_user_manager).action_attendance_sheet_done()
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_basic).write({"date_start": "2023-02-02"})

        # TEST32: error if basic employee tries to update attendance on approved sheet
        with self.assertRaises(UserError):
            self.test_attendance1.with_user(self.test_user_basic).write(
                {"check_in": "2023-01-10 08:00"}
            )

        # TEST33: permission error locking/unlocking done sheet
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_basic).action_attendance_sheet_lock()
        sheet.with_user(self.test_user_manager).action_attendance_sheet_lock()
        with self.assertRaises(UserError):
            sheet.with_user(self.test_user_basic).action_attendance_sheet_unlock()

    def test_auto_lunch_scenario(self):
        # TEST34: If attendance auto lunch set true when it shouldn't be
        company = self.env.company
        company.write(
            {
                "use_attendance_sheets": True,
                "auto_lunch": True,
                "auto_lunch_duration": 5,
                "auto_lunch_hours": 0.5,
                "date_start": "2023-02-01",
                "date_end": "2023-02-08",
            }
        )
        self.AttendanceSheet._create_sheet_id()
        self.test_attendance_no_lunch = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-15 08:00",
                "check_out": "2023-01-15 12:00",
                "auto_lunch": True,
            }
        )
        self.assertTrue(self.test_attendance_no_lunch.auto_lunch)

        # TEST35: clock-in button method on sheet
        sheet = self.env["hr.attendance.sheet"].search([], limit=1)
        sheet.attendance_ids.unlink()
        sheet.attendance_action_change()
        self.assertEqual(len(sheet.attendance_ids), 1)

    def test_attendance_admin(self):
        # TEST36: Test possible reviewers with dept admin & employee_manager policy
        company = self.env.company
        company.write(
            {
                "use_attendance_sheets": True,
                "attendance_sheet_review_policy": "employee_manager",
                "date_start": "2023-02-01",
                "date_end": "2023-02-08",
            }
        )
        self.test_admin = self.env["hr.employee"].create({"name": "TestAdmin"})
        self.test_department1 = self.env["hr.department"].create(
            {
                "name": "Test Department",
                "attendance_admin": self.test_admin.id,
            }
        )
        self.test_employee.write({"department_id": self.test_department1.id})
        self.AttendanceSheet._create_sheet_id()
        self.test_attendance_no_lunch = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-15 12:00",
                "check_out": "2023-01-15 12:00",
                "auto_lunch": True,
            }
        )
        sheet = self.env["hr.attendance.sheet"].search([], limit=1)
        sheet._get_possible_reviewers()
        self.assertEqual(len(sheet._get_possible_reviewers()), 2)

        # TEST37: Test possible reviewers with dept admin & hr_or_manager policy
        company.write({"attendance_sheet_review_policy": "hr_or_manager"})
        sheet._get_possible_reviewers()
        self.assertEqual(len(sheet._get_possible_reviewers()), 7)

    def test_auto_lunch_time_between_too_small_scenario(self):
        # TEST38: If attendances are within same day but < lunch duration.
        company = self.env.company
        company.write(
            {
                "use_attendance_sheets": True,
                "auto_lunch": True,
                "auto_lunch_duration": 5,
                "auto_lunch_hours": 1,
                "date_start": "2023-01-01",
                "date_end": "2023-01-15",
            }
        )
        self.AttendanceSheet._create_sheet_id()
        self.test_attendance_lunch1 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-13 08:00",
                "check_out": "2023-01-13 14:00",
            }
        )
        self.test_attendance_lunch2 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": "2023-01-14 14:15",
                "check_out": "2023-01-14 18:15",
            }
        )
        self.test_attendance_lunch1._compute_duration()
        # create attendance_sheet
        self.assertTrue(self.test_attendance_lunch1.auto_lunch)

    def test_action_attendance_sheet_confirm(self):
        self.test_user_employee_test = new_test_user(
            self.env,
            login="test_user@test.com",
            groups="hr_attendance.group_hr_attendance_manager",
            context=self.ctx_new_test_user,
        )
        self.test_employee_test = self.env["hr.employee"].create(
            {
                "name": "TestEmployeeTest",
                "user_id": self.test_user_employee_test.id,
                "parent_id": self.test_manager.id,
                "hours_to_work": 20.0,
            }
        )
        attednance_sheet = self.env["hr.attendance.sheet"].create(
            {
                "employee_id": self.test_employee_test.id,
                "date_start": "2023-02-01",
                "date_end": "2023-02-08",
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "employee_id": self.test_employee_test.id,
                            "check_in": "2023-02-01 13:00",
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            attednance_sheet.with_user(
                self.test_user_employee_test
            ).action_attendance_sheet_confirm()
        company = self.env.company
        company.write({"attendance_sheet_review_policy": "hr_or_manager"})
        attednance_sheet.write({"can_review": False})
        with self.assertRaises(UserError):
            attednance_sheet._check_can_review()
        company.write(
            {
                "use_attendance_sheets": True,
                "date_end": "2023-01-31",
            }
        )
        attednance_sheet.check_pay_period_dates()
        attednance_sheet_check_out = self.env["hr.attendance.sheet"].create(
            {
                "employee_id": self.test_employee_test.id,
                "date_start": "2023-02-01",
                "date_end": "2023-02-08",
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "employee_id": self.test_employee_test.id,
                            "check_in": "2023-02-01 13:00",
                            "check_out": "2023-02-01 14:00",
                        },
                    )
                ],
            }
        )
        attednance_sheet_check_out.with_user(
            self.test_user_employee_test
        ).action_attendance_sheet_confirm()
        attednance_sheet = self.env["hr.attendance.sheet"].create(
            {
                "employee_id": self.test_employee_test.id,
                "date_start": "2023-02-01",
                "date_end": "2023-02-08",
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "employee_id": self.test_employee_test.id,
                            "check_in": "2023-02-01 00:00",
                            "check_out": "2023-02-01 00:00",
                        },
                    )
                ],
            }
        )
        attednance_sheet.with_user(
            self.test_user_employee_test
        ).action_attendance_sheet_confirm()

        attednance_sheet_check_out = self.env["hr.attendance.sheet"].create(
            {
                "employee_id": self.test_employee_test.id,
                "date_start": "2023-02-01",
                "date_end": "2023-02-08",
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "employee_id": self.test_employee_test.id,
                            "check_in": "2023-02-01 15:00",
                            "check_out": "2023-02-01 16:00",
                        },
                    )
                ],
            }
        )
        attednance_sheet_check_out.with_user(
            self.test_user_employee_test
        ).action_attendance_sheet_confirm()
        sheet = self.env["hr.attendance.sheet"].create(
            {
                "employee_id": self.test_employee_test.id,
                "date_start": "2023-02-01",
                "date_end": "2023-02-08",
            }
        )
        vals = {
            "employee_id": attednance_sheet_check_out.employee_id.id,
            "check_in": "2023-02-01 17:00",
            "check_out": "2023-02-01 18:00",
        }
        hr_attendance = self.env["hr.attendance"].create(vals)
        hr_attendance.write({"attendance_sheet_id": sheet.id})
        hr_attendance.attendance_sheet_id.with_user(
            self.test_user_employee_test
        ).action_attendance_sheet_confirm()
        hr_attendance.attendance_sheet_id.with_user(
            self.test_user_employee_test
        ).action_attendance_sheet_done()
        with self.assertRaises(UserError):
            sheet.write({"can_review": True})
            hr_attendance._get_attendance_state()
        company.write(
            {
                "use_attendance_sheets": True,
                "date_start": "2023-02-01",
                "attendance_sheet_range": "WEEKLY",
                "auto_lunch": True,
                "auto_lunch_duration": 0.5,
                "auto_lunch_hours": 6.0,
            }
        )
        self.test_attendance_lunch = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee_test.id,
                "check_in": "2023-01-26 14:00",
                "check_out": "2023-01-26 15:00",
            }
        )
        self.test_attendance_lunch_new = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee_test.id,
                "check_in": "2023-01-26 19:00",
                "check_out": "2023-01-26 20:00",
            }
        )
        self.test_attendance_lunch._compute_duration()

        self.attendance_lunch_2 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee_test.id,
                "check_in": "2023-01-30 14:00",
                "check_out": "2023-01-30 15:00",
            }
        )
        self.attendance_lunch_3 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee_test.id,
                "check_in": "2023-01-30 16:00",
                "check_out": "2023-01-30 17:00",
            }
        )
        self.attendance_lunch_3._compute_duration()

        company.write(
            {
                "use_attendance_sheets": True,
                "date_start": "2023-02-01",
                "attendance_sheet_range": "WEEKLY",
                "auto_lunch": True,
                "auto_lunch_duration": 0.5,
                "auto_lunch_hours": 3.0,
            }
        )
        self.attendance_lunch = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee_test.id,
                "check_in": "2023-01-30 18:00",
                "check_out": "2023-01-30 19:00",
            }
        )
        self.attendance_lunch._compute_duration()

        company.write(
            {
                "use_attendance_sheets": True,
                "date_start": "2023-02-01",
                "attendance_sheet_range": "WEEKLY",
                "auto_lunch": True,
                "auto_lunch_duration": 0.5,
                "auto_lunch_hours": 3.0,
            }
        )
        self.attendance_lunch_1 = self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee_test.id,
                "check_in": "2023-01-25 00:00",
                "check_out": "2023-01-25 00:00",
                "auto_lunch": True,
            }
        )
        self.attendance_lunch_1._compute_duration()

        company.write(
            {
                "attendance_sheet_range": "MONTHLY",
                "attendance_sheet_review_policy": "employee_manager",
                "date_start": "2023-02-01",
                "date_end": "2023-02-15",
            }
        )
        company.onchange_attendance_sheet_range()
