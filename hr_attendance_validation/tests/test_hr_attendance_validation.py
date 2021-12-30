# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import date

from freezegun import freeze_time

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestHrAttendanceValidation(TransactionCase):
    def setup_employee(self):
        employee_group = self.env.ref("hr_attendance.group_hr_attendance_user")
        self.user_employee = self.env["res.users"].create(
            {
                "name": "Test User Employee 1",
                "login": "test 1",
                "email": "test1@test.com",
                "groups_id": [(6, 0, [employee_group.id])],
                "tz": "UTC",
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee 1",
                "tz": "UTC",
                "user_id": self.user_employee.id,
            }
        )
        self.employee2 = self.env["hr.employee"].create(
            {
                "name": "Employee 2 without user",
                "tz": "UTC",
            }
        )

    def setup_employee_allocation(self):
        self.env["hr.leave.allocation"].create(
            {
                "employee_id": self.employee2.id,
                "holiday_status_id": self.leave_comp.id,
                "number_of_days": 10,
                "holiday_type": "employee",
                "state": "validate",
                "name": "10 days - Compensatory hours",
            }
        )

    def setup_employee_holidays(self):
        self.env["hr.leave.allocation"].create(
            {
                "employee_id": self.employee.id,
                "holiday_status_id": self.leave_cl.id,
                "number_of_days": 30,
                "holiday_type": "employee",
                "state": "validate",
            }
        )
        self.empl_leave = self.env["hr.leave"].create(
            {
                "employee_id": self.employee.id,
                "holiday_status_id": self.leave_cl.id,
                # overlap two weeks
                "request_date_from": "2021-12-01",
                "request_date_to": "2021-12-08",
                "number_of_days": 6,
            }
        )
        self.empl_leave.action_validate()

        self.env["hr.leave.allocation"].create(
            {
                "employee_id": self.employee.id,
                "holiday_status_id": self.leave_comp.id,
                "number_of_days": 1,
                "holiday_type": "employee",
                "state": "validate",
            }
        )
        self.empl_leave_comp = self.env["hr.leave"].create(
            {
                "employee_id": self.employee.id,
                "holiday_status_id": self.leave_comp.id,
                "request_date_from": "2021-12-10",
                "request_hour_from": "8",
                "request_hour_to": "12",
                "request_unit_hours": True,
                "number_of_days": 0.5,
            }
        )
        self.empl_leave_comp.action_validate()

    def setup_employee_attendances(self):
        self.env["hr.attendance"].create(
            [
                {  # testing record before not considered
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-05 07:30:00",
                    "check_out": "2021-12-05 08:00:00",
                },
                {  # testing other employee
                    "employee_id": self.employee2.id,
                    "check_in": "2021-12-06 08:00:00",
                    "check_out": "2021-12-06 12:00:00",
                },
                {
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-09 07:30:00",
                    "check_out": "2021-12-09 08:00:00",
                    "is_overtime": True,
                },
                {
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-09 08:00:00",
                    "check_out": "2021-12-09 12:00:00",
                    "is_overtime": False,
                },
                {
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-09 13:00:00",
                    "check_out": "2021-12-09 17:00:00",
                    "is_overtime": False,
                },
                {
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-10 14:00:00",
                    "check_out": "2021-12-10 17:00:00",
                    "is_overtime": False,
                },
                {
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-10 17:00:00",
                    "check_out": "2021-12-10 18:30:00",
                    "is_overtime": True,
                    "is_overtime_due": True,
                },
                {  # testing record after not considered
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-13 07:30:00",
                    "check_out": "2021-12-13 08:00:00",
                },
            ]
        )

    def setUp(self):
        super().setUp()
        self.HrAttendance = self.env["hr.attendance"]
        self.HrAttendanceValidation = self.env["hr.attendance.validation.sheet"]
        self.leave_cl = self.env.ref("hr_holidays.holiday_status_cl")
        self.leave_comp = self.env.ref("hr_holidays.holiday_status_comp")
        self.setup_employee()
        self.setup_employee_allocation()
        self.setup_employee_holidays()
        self.setup_employee_attendances()

    def test_name_get_missing_employee(self):
        with freeze_time("2021-12-12 20:45", tz_offset=0):
            new_element = self.HrAttendanceValidation.new({})
            self.assertEqual(new_element.name_get()[0][1], "Week 48 - False")

    def test_require_regeneration(self):
        validation_sheet = self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee.id,
                "date_from": "2021-12-13",
                "date_to": "2021-12-19",
            }
        )
        validation_sheet.action_retrieve_attendance_and_leaves()
        with Form(validation_sheet) as form:
            self.assertFalse(form.require_regeneration)
            form.employee_id = self.employee2
            self.assertTrue(form.require_regeneration)
            form.save()
        self.assertTrue(validation_sheet)
        validation_sheet.action_retrieve_attendance_and_leaves()
        self.assertFalse(validation_sheet.require_regeneration)

    def test_name_get_multi(self):
        weeks = self.validate_week()
        weeks += self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee.id,
                "date_from": "2021-12-13",
                "date_to": "2021-12-19",
            }
        )
        res = weeks.name_get()
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][1], "Week 49 - Employee 1")
        self.assertEqual(res[1][1], "Week 50 - Employee 1")

    def test_default_from_date(self):
        with freeze_time("2021-12-12 20:45", tz_offset=0):
            new_element = self.HrAttendanceValidation.new({})
            self.assertEqual(new_element.date_from, date(2021, 11, 29))
            self.assertEqual(new_element.date_to, date(2021, 12, 5))

        with freeze_time("2021-12-13 06:45", tz_offset=0):
            new_element = self.HrAttendanceValidation.new({})
            self.assertEqual(new_element.date_from, date(2021, 12, 6))
            self.assertEqual(new_element.date_to, date(2021, 12, 12))

        with freeze_time("2021-12-14 06:45", tz_offset=0):
            new_element = self.HrAttendanceValidation.new({})
            self.assertEqual(new_element.date_from, date(2021, 12, 6))
            self.assertEqual(new_element.date_to, date(2021, 12, 12))

    def test_action_retrieve_attendance_and_leaves(self):
        validation = self.HrAttendanceValidation.new(
            {
                "employee_id": self.employee.id,
            }
        )
        validation.action_retrieve_attendance_and_leaves()
        self.assertFalse(validation.leave_ids)
        self.assertFalse(validation.attendance_ids)
        validation.date_from = "2021-12-06"
        validation.date_to = "2021-12-12"
        validation.action_retrieve_attendance_and_leaves()
        self.assertEqual(len(validation.leave_ids), 2)
        self.assertEqual(validation.leave_hours, 28)
        self.assertEqual(len(validation.attendance_ids), 5)

    def test_action_retrieve_leaves_outer_validation_date(self):
        validation = self.HrAttendanceValidation.new(
            {
                "employee_id": self.employee.id,
            }
        )
        validation.date_from = "2021-12-07"
        validation.date_to = "2021-12-08"
        validation.action_retrieve_attendance_and_leaves()
        self.assertEqual(len(validation.leave_ids), 1)
        self.assertEqual(validation.leave_hours, 16)

    def test_computed_fields_base(self):
        # resource.resource_calendar_std is 40 hours/week
        # from 8 to 12 and 13 to 17
        validation = self.HrAttendanceValidation.new(
            {
                "employee_id": self.employee.id,
                "date_from": "2021-12-06",
                "date_to": "2021-12-12",
            }
        )
        validation.action_retrieve_attendance_and_leaves()
        self.assertEqual(validation.theoretical_hours, 40)
        self.assertEqual(validation.attendance_hours, 11)
        self.assertEqual(validation.overtime_due_hours, 1.5)
        self.assertEqual(validation.attendance_total_hours, 12.5)
        self.assertEqual(validation.overtime_not_due_hours, 0.5)
        self.assertEqual(validation.leave_hours, 3 * 8 + 0.5 * 8)
        self.assertEqual(validation.compensatory_hour, 0.5)
        self.assertEqual(validation.regularization_compensatory_hour_taken, 0)

    def test_generate_compensatory(self):
        leaves_before = self.leave_comp.with_context(
            employee_id=self.employee.id
        ).remaining_leaves
        validation = self.validate_week()
        self.assertEqual(validation.state, "validated")
        self.assertEqual(
            validation.leave_allocation_id.holiday_status_id.id, self.leave_comp.id
        )
        self.leave_comp.refresh()
        self.assertEqual(
            self.leave_comp.with_context(employee_id=self.employee.id).remaining_leaves,
            leaves_before + 0.5,
        )
        self.assertTrue(
            validation.leave_allocation_id.name,
        )
        self.assertEqual(
            validation.leave_allocation_id.notes,
            "Allocation created and validated from attendance "
            "validation reviews: Week 49 - Employee 1",
        )

    def test_generate_leaves(self):
        leaves_before = self.leave_comp.with_context(
            employee_id=self.employee2.id
        ).remaining_leaves

        validation = self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee2.id,
                "date_from": "2021-12-06",
                "date_to": "2021-12-12",
            }
        )
        validation.action_retrieve_attendance_and_leaves()
        validation.action_validate()
        self.assertEqual(validation.state, "validated")
        self.assertEqual(validation.leave_id.holiday_status_id.id, self.leave_comp.id)
        self.leave_comp.refresh()
        self.assertEqual(validation.regularization_compensatory_hour_taken, 36)
        self.assertEqual(
            self.leave_comp.with_context(
                employee_id=self.employee2.id
            ).remaining_leaves,
            leaves_before - validation.regularization_compensatory_hour_taken,
        )
        self.assertEqual(
            validation.leave_id.name,
            "Compensatory hours regularization generated from "
            "Week 49 - Employee 2 without user",
        )

    def validate_week(self):
        validation = self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee.id,
                "date_from": "2021-12-06",
                "date_to": "2021-12-12",
            }
        )
        validation.action_retrieve_attendance_and_leaves()
        validation.action_validate()
        return validation

    def test_could_not_create_employee_attendance_on_validated_week(self):
        self.validate_week()
        with self.assertRaisesRegex(
            ValidationError,
            "Cannot create new attendance for employee Employee 1. "
            "Attendance for the day of the check in 2021-12-12 has already been "
            "reviewed and validated.",
        ):
            self.env["hr.attendance"].create(
                [
                    {
                        "employee_id": self.employee.id,
                        "check_in": "2021-12-12 08:00:00",
                        "check_out": "2021-12-12 12:00:00",
                    },
                ]
            )

    def test_create_employee_attendance_on_validated_week(self):
        self.validate_week()
        self.env["hr.attendance"].create(
            [
                {  # testing record before if fine
                    "employee_id": self.employee.id,
                    "check_in": "2021-12-05 20:30:00",
                    "check_out": "2021-12-05 21:00:00",
                },
                {  # testing other employee is ok
                    "employee_id": self.employee2.id,
                    "check_in": "2021-12-06 20:00:00",
                    "check_out": "2021-12-06 21:00:00",
                },
            ]
        )

    def test_unlink_attendance(self):
        att = self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee.id), ("check_in", ">", "2021-12-12")]
        )
        att.ensure_one()
        self.assertTrue(att.unlink())
        self.assertEqual(
            self.env["hr.attendance"].search_count(
                [
                    ("employee_id", "=", self.employee.id),
                    ("check_in", ">", "2021-12-12"),
                ]
            ),
            0,
        )

    def test_unlink_attendance_forbiden(self):
        self.validate_week()
        attendances = self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee.id)]
        )
        with self.assertRaisesRegex(
            ValidationError,
            r"Can not remove this attendance \(Employee 1, .*\) "
            "which has been already reviewed and validated.",
        ):
            attendances.unlink()

    def test_write_attendance(self):
        att = self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee.id), ("check_in", ">", "2021-12-12")]
        )
        att.ensure_one()
        att.write({"is_overtime_due": True})

    def test_write_attendance_forbiden(self):
        self.validate_week()
        attendances = self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee.id)]
        )
        with self.assertRaisesRegex(
            ValidationError,
            r"Can not change this attendance \(Employee 1, .*\) "
            "which has been already reviewed and validated.",
        ):
            attendances.write({"is_overtime_due": True})

    def test_write_attendance_forbiden_after_change(self):
        self.validate_week()
        attendances = self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee.id), ("check_in", ">", "2021-12-12")]
        )
        with self.assertRaisesRegex(
            ValidationError,
            r"Can not change this attendance \(Employee 1, 2021-12-12\) "
            "which would be moved to a validated day.",
        ):
            attendances.write(
                {"check_in": "2021-12-12 22:00", "check_out": "2021-12-12 23:00"}
            )

    def test_generate_reviews(self):
        reviews = self.HrAttendanceValidation.generate_reviews()
        self.assertEqual(len(reviews), self.env["hr.employee"].search_count([]))

    def test_avoid_duplicated_allocation(self):
        # in case allocation is generated
        # we come back to draft mode "to review", removing the
        # previously created allocatoin is left to the user
        # once re-validate avoid duplication in allocation
        count_before = self.env["hr.leave.allocation"].search_count([])
        attenance_review_week = self.validate_week()
        self.assertEqual(
            self.env["hr.leave.allocation"].search_count([]), count_before + 1
        )
        attenance_review_week.action_to_review()
        self.assertEqual(
            self.env["hr.leave.allocation"].search_count([]), count_before + 1
        )
        self.assertEqual(attenance_review_week.state, "draft")
        self.assertTrue(attenance_review_week.leave_allocation_id)
        attenance_review_week.action_validate()
        self.assertEqual(
            self.env["hr.leave.allocation"].search_count([]), count_before + 1
        )
        self.assertEqual(attenance_review_week.state, "validated")
        self.assertTrue(attenance_review_week.leave_allocation_id)

    def test_employee_check_in_out(self):
        # in check-in/check-out processus odoo make sure
        # the week is not already validated which require
        # access to
        # `hr.attendance.validation.sheet`'s records
        employee = self.employee.with_user(self.user_employee)
        with freeze_time("2021-12-30 09:01", tz_offset=0):
            employee._attendance_action_change()
        with freeze_time("2021-12-30 11:01", tz_offset=0):
            employee._attendance_action_change()

    def test_user_can_read_validated_sheet_only(self):
        # employee = self.employee.with_user(self.user_employee)
        validation = self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee.id,
                "date_from": "2021-12-06",
                "date_to": "2021-12-12",
            }
        )
        validation.action_retrieve_attendance_and_leaves()

        HrAttendanceValidationEmployee = self.HrAttendanceValidation.with_user(
            self.user_employee
        )
        self.assertEqual(HrAttendanceValidationEmployee.search_count([]), 0)
        with self.assertRaisesRegex(AccessError, "Due to security restrictions.*"):
            validation.with_user(self.user_employee).read(["date_from"])
        validation.action_validate()
        self.assertEqual(HrAttendanceValidationEmployee.search_count([]), 1)
        validation.with_user(self.user_employee).read(["date_from"])

    def test_user_cant_read_others_sheets(self):
        # employee = self.employee.with_user(self.user_employee)
        validation = self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee2.id,
                "date_from": "2021-12-06",
                "date_to": "2021-12-12",
            }
        )
        validation.action_retrieve_attendance_and_leaves()

        HrAttendanceValidationEmployee = self.HrAttendanceValidation.with_user(
            self.user_employee
        )
        self.assertEqual(HrAttendanceValidationEmployee.search_count([]), 0)
        with self.assertRaisesRegex(AccessError, "Due to security restrictions.*"):
            validation.with_user(self.user_employee).read(["date_from"])
        validation.action_validate()
        self.assertEqual(HrAttendanceValidationEmployee.search_count([]), 0)
        with self.assertRaisesRegex(AccessError, "Due to security restrictions.*"):
            validation.with_user(self.user_employee).read(["date_from"])

    def test_employee_works_hours(self):
        with freeze_time("2021-12-10 19:45", tz_offset=0):
            self.assertEqual(self.employee.hours_current_week, 12.5)
            self.assertEqual(self.employee.hours_last_month, 0)
            self.assertEqual(self.employee.hours_today, 4.5)

    def test_employee_works_hours_month_before(self):
        with freeze_time("2022-01-10 19:45", tz_offset=0):
            self.assertEqual(self.employee.hours_current_week, 0)
            self.assertEqual(self.employee.hours_last_month, 13.5)
            self.assertEqual(self.employee.hours_today, 0)
