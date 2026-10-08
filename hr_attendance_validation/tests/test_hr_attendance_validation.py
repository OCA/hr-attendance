# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import date

from freezegun import freeze_time

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase

from odoo.addons.hr_attendance_validation.controllers.main import (
    HrAttendanceValidation as controller,
)


class TestHrAttendanceValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.hr_attendance_overtime = True
        cls.env.company.overtime_start_date = "2021-01-01"
        cls.setup_employees()
        cls.setup_public_holidays()
        cls.setup_leave_type()
        cls.setup_employees_allocations()
        cls.setup_employee_holidays()
        cls.setup_employee_attendances()

    @classmethod
    def setup_employees(cls):
        cls.user_employee = cls.env["res.users"].create(
            {
                "name": "Test User Employee 1",
                "login": "test 1",
                "email": "test1@test.com",
                "groups_id": [
                    (
                        6,
                        0,
                        (
                            cls.env.ref("hr_attendance.group_hr_attendance_own_reader")
                            | cls.env.ref("base.group_user")
                        ).ids,
                    )
                ],
                "tz": "UTC",
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Employee 1",
                "weekly_attendance_validation": True,
                "tz": "UTC",
                "user_id": cls.user_employee.id,
            }
        )
        cls.employee2 = cls.env["hr.employee"].create(
            {
                "name": "Employee 2 without user",
                "weekly_attendance_validation": True,
                "tz": "UTC",
            }
        )
        cls.employee3 = cls.env["hr.employee"].create(
            {
                "name": "Employee 3 daily contract",
                "weekly_attendance_validation": False,
                "tz": "UTC",
            }
        )

    @classmethod
    def setup_public_holidays(cls):
        public_holidays_2021 = cls.env["hr.holidays.public"].create(
            {
                "year": 2021,
                "country_id": cls.employee.address_id.country_id.id,
            }
        )
        cls.env["hr.holidays.public.line"].create(
            {
                "name": "Fête nationale",
                "date": "2021-07-14",
                "year_id": public_holidays_2021.id,
            }
        )

    @classmethod
    def setup_leave_type(cls):
        cls.leave_type_paid_time_off = cls.env.ref("hr_holidays.holiday_status_cl")
        cls.leave_type_compensatory = cls.env.ref(
            "hr_holidays_attendance.holiday_status_extra_hours"
        )
        cls.leave_type_compensatory.allows_negative = True
        cls.leave_type_compensatory.max_allowed_negative = 100
        cls.leave_type_other_hourly_paid_time_off = cls.env["hr.leave.type"].create(
            {
                "name": "Hourly paid off",
                "request_unit": "half_day",
                "color": 2,
                "overtime_deductible": False,
                "requires_allocation": "yes",
                "employee_requests": "yes",
                "allocation_validation_type": "no",
                "time_type": "leave",
                "allows_negative": True,
                "max_allowed_negative": 10,
                "leave_validation_type": "no_validation",
                "create_calendar_meeting": True,
            }
        )
        cls.leave_type_remote = cls.env["hr.leave.type"].create(
            {
                "name": "Remote time",
                "request_unit": "half_day",
                "color": 2,
                "overtime_deductible": False,
                "requires_allocation": "yes",
                "employee_requests": "yes",
                "allocation_validation_type": "no",
                "time_type": "other",
                "allows_negative": True,
                "max_allowed_negative": 10,
                "leave_validation_type": "no_validation",
                "create_calendar_meeting": True,
            }
        )
        cls.leave_type_compensatory2 = cls.env.ref(
            "hr_holidays_attendance.holiday_status_extra_hours"
        ).copy({"name": "Compensatory 2"})

    @classmethod
    def setup_employees_allocations(cls):
        allocations = cls.env["hr.leave.allocation"].create(
            [
                {
                    "employee_id": cls.employee.id,
                    "holiday_status_id": cls.leave_type_paid_time_off.id,
                    "number_of_days": 40,
                    "holiday_type": "employee",
                    "date_from": "2021-01-01",
                    "date_to": "2021-12-31",
                    "state": "confirm",
                },
                {
                    "employee_id": cls.employee.id,
                    "holiday_status_id": cls.leave_type_other_hourly_paid_time_off.id,
                    "number_of_days": 20,
                    "holiday_type": "employee",
                    "date_from": "2021-01-01",
                    "date_to": "2021-12-31",
                    "state": "confirm",
                },
                {
                    "employee_id": cls.employee.id,
                    "holiday_status_id": cls.leave_type_remote.id,
                    "number_of_days": 5,
                    "holiday_type": "employee",
                    "name": "5 days - Remote days",
                    "date_from": "2021-01-01",
                    "date_to": "2021-12-31",
                    "state": "confirm",
                },
                {
                    "employee_id": cls.employee3.id,
                    "holiday_status_id": cls.leave_type_paid_time_off.id,
                    "number_of_days": 40,
                    "holiday_type": "employee",
                    "date_from": "2021-01-01",
                    "date_to": "2021-12-31",
                    "state": "confirm",
                },
            ]
        )
        allocations.filtered(
            lambda allocation: allocation.state != "validate"
        ).action_validate()
        assert all(
            allocations.mapped(lambda allocation: allocation.state == "validate")
        )

    @classmethod
    def setup_employee_holidays(cls):
        cls.empl_leave = cls.env["hr.leave"].create(
            {
                "employee_id": cls.employee.id,
                "holiday_status_id": cls.leave_type_paid_time_off.id,
                # overlap two weeks
                "request_date_from": "2021-12-01",
                "request_date_to": "2021-12-08",
                "number_of_days": 6,
            }
        )
        cls.empl_leave.action_validate()
        assert cls.empl_leave.state == "validate"
        cls.empl_leave_hour = cls.env["hr.leave"].create(
            {
                "employee_id": cls.employee.id,
                "holiday_status_id": cls.leave_type_other_hourly_paid_time_off.id,
                "request_date_from": "2021-12-09",
                "request_date_to": "2021-12-09",
                "request_hour_from": "10",
                "request_hour_to": "12",
                "request_unit_hours": True,
            }
        )
        # cls.empl_leave.action_validate()
        assert cls.empl_leave_hour.state == "validate"
        cls.empl_leave_comp = cls.env["hr.leave"].create(
            {
                "employee_id": cls.employee.id,
                "holiday_status_id": cls.leave_type_compensatory.id,
                "request_date_from": "2021-12-09",
                "request_date_to": "2021-12-09",
                "request_hour_from": "14",
                "request_hour_to": "16",
                "request_unit_hours": True,
            }
        )

        cls.empl_leave_comp.action_validate()
        assert cls.empl_leave_comp.state == "validate"
        cls.empl_remote = cls.env["hr.leave"].create(
            {
                "employee_id": cls.employee.id,
                "holiday_status_id": cls.leave_type_remote.id,
                # overlap two weeks
                "request_date_from": "2021-12-10",
                "request_date_to": "2021-12-10",
                "request_hour_from": "14",
                "request_hour_to": "17",
                "number_of_days": 0.5,
            }
        )
        cls.empl_remote.action_validate()
        assert cls.empl_remote.state == "validate"
        cls.empl_leave = cls.env["hr.leave"].create(
            {
                "employee_id": cls.employee3.id,
                "holiday_status_id": cls.leave_type_paid_time_off.id,
                # overlap two weeks
                "request_date_from": "2021-12-07",
                "request_date_to": "2021-12-08",
                "number_of_days": 2,
            }
        )
        cls.empl_leave.action_validate()
        assert cls.empl_leave.state == "validate"

    @classmethod
    def setup_employee_attendances(cls):
        cls.env["hr.attendance"].create(
            [
                {  # testing record before not considered
                    "employee_id": cls.employee.id,
                    "check_in": "2021-12-05 07:30:00",
                    "check_out": "2021-12-05 08:00:00",
                },
                {  # testing other employee
                    "employee_id": cls.employee2.id,
                    "check_in": "2021-12-06 08:00:00",
                    "check_out": "2021-12-06 12:00:00",
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": "2021-12-09 07:30:00",
                    "check_out": "2021-12-09 08:00:00",
                    "is_overtime": True,
                    "is_overtime_due": False,
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": "2021-12-09 08:00:00",
                    "check_out": "2021-12-09 12:00:00",
                    "is_overtime": False,
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": "2021-12-09 13:00:00",
                    "check_out": "2021-12-09 17:00:00",
                    "is_overtime": False,
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": "2021-12-10 14:00:00",
                    "check_out": "2021-12-10 17:00:00",
                    "is_overtime": False,
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": "2021-12-10 17:00:00",
                    "check_out": "2021-12-10 18:30:00",
                    "is_overtime": True,
                    "is_overtime_due": True,
                },
                {  # testing record after not considered
                    "employee_id": cls.employee.id,
                    "check_in": "2021-12-13 07:30:00",
                    "check_out": "2021-12-13 08:00:00",
                },
                {  # employee 3 should create overtime
                    "employee_id": cls.employee3.id,
                    "check_in": "2021-12-06 07:30:00",
                    "check_out": "2021-12-06 19:30:00",
                },
                {
                    "employee_id": cls.employee3.id,
                    "check_in": "2021-12-09 09:00:00",
                    "check_out": "2021-12-09 12:00:00",
                },
                {
                    "employee_id": cls.employee3.id,
                    "check_in": "2021-12-09 14:00:00",
                    "check_out": "2021-12-09 17:00:00",
                },
            ]
        )

    def setUp(self):
        super().setUp()
        self.HrAttendanceValidation = self.env["hr.attendance.validation.sheet"]

    def test_controller_get_user_attendance_data(self):
        data = controller._get_user_attendance_data(self.employee)
        # make sure overload from hr_attendance_overtime is still present
        self.assertTrue("overtime_info" in data)
        self.assertTrue("hours_current_week" in data)

    def test_controller_get_user_attendance_data_no_employee(self):
        data = controller._get_user_attendance_data(False)
        self.assertTrue("hours_current_week" not in data)

    def test_new_without_calendar(self):
        validation = self.HrAttendanceValidation.new({})

        self.assertFalse(validation.calendar_id)
        self.assertEqual(validation.theoretical_hours, 0)

    def test_name_get_missing_employee(self):
        with freeze_time("2021-12-12 20:45", tz_offset=0):
            new_element = self.HrAttendanceValidation.new({})
            self.assertEqual(new_element.display_name, "Week 48 - False")

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
        res = weeks.mapped("display_name")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], "Week 49 - Employee 1")
        self.assertEqual(res[1], "Week 50 - Employee 1")

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
        # 2 hours are compensatory leaves that are not retrieve
        # from hr leaves
        self.assertEqual(validation.leave_hours, 3 * 8 + 2 + 2)
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
        self.assertEqual(validation.leave_hours, 3 * 8 + 0.25 * 8 + 0.25 * 8)
        self.assertEqual(validation.compensatory_leave_hours, 0.25 * 8)
        self.assertEqual(validation.compensatory_hour, 0.5)
        self.assertEqual(validation.regularization_compensatory_hour_taken, 0)

    def test_generate_compensatory(self):
        self.assertEqual(self.employee.total_overtime, -2)
        validation = self.validate_week()
        self.assertEqual(validation.state, "validated")
        self.assertEqual(validation.adjustment_overtime_id.duration, 0.5)
        self.assertEqual(self.employee.total_overtime, -1.5)

    def test_generate_leaves(self):
        self.assertEqual(self.employee2.total_overtime, 0)

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
        self.assertEqual(validation.adjustment_overtime_id.duration, -36)
        self.assertEqual(self.employee2.total_overtime, -36)
        self.assertEqual(
            self.leave_type_compensatory.with_context(
                employee_id=self.employee2.id
            ).display_name,
            f"{self.leave_type_compensatory.name} (36:00 credit hours)",
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
            r"Can not edit attendance \(Employee 1, "
            r"2021-12-12\) which try to update a validated period.",
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
            r"Can not change this attendance \(Employee 1,.*\) "
            r"which has been already reviewed and validated.",
        ):
            attendances.write({"is_overtime_due": True})

    def test_write_attendance_forbiden_after_change(self):
        self.validate_week()
        attendances = self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee.id), ("check_in", ">", "2021-12-12")]
        )
        with self.assertRaisesRegex(
            ValidationError,
            r"Can not edit attendance \(Employee 1, 2021-12-12\) "
            r"which try to update a validated period.",
        ):
            attendances.write(
                {"check_in": "2021-12-12 22:00", "check_out": "2021-12-12 23:00"}
            )

    def test_generate_reviews(self):
        reviews = self.HrAttendanceValidation.generate_reviews()
        self.assertEqual(len(reviews), 2)

    def test_avoid_duplicated_allocation(self):
        # in case allocation is generated
        # we come back to draft mode "to review", removing the
        # previously created allocation
        count_before = self.env["hr.attendance.overtime"].search_count([])
        attenance_review_week = self.validate_week()
        self.assertTrue(attenance_review_week.adjustment_overtime_id)
        initial_duration = attenance_review_week.adjustment_overtime_id.duration
        self.assertEqual(
            self.env["hr.attendance.overtime"].search_count([]), count_before + 1
        )
        attenance_review_week.action_to_review()
        self.assertEqual(
            self.env["hr.attendance.overtime"].search_count([]), count_before
        )
        self.assertEqual(attenance_review_week.state, "draft")
        self.assertFalse(attenance_review_week.adjustment_overtime_id)
        attenance_review_week.action_validate()
        self.assertEqual(
            self.env["hr.attendance.overtime"].search_count([]), count_before + 1
        )
        self.assertEqual(attenance_review_week.state, "validated")
        self.assertTrue(attenance_review_week.adjustment_overtime_id)
        self.assertEqual(
            attenance_review_week.adjustment_overtime_id.duration, initial_duration
        )

    def test_employee_check_in_out(self):
        # in check-in/check-out processus odoo make sure
        # the week is not already validated which require
        # access to
        # `hr.attendance.validation.sheet`'s records
        employee = self.employee.with_user(self.user_employee)
        with freeze_time("2021-12-30 09:01", tz_offset=0):
            employee.sudo()._attendance_action_change()
        with freeze_time("2021-12-30 11:01", tz_offset=0):
            employee.sudo()._attendance_action_change()

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
        with self.assertRaisesRegex(
            AccessError, r".*doesn\'t have \'read\' access to.*"
        ):
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
        with self.assertRaisesRegex(
            AccessError, r".*doesn\'t have \'read\' access to.*"
        ):
            validation.with_user(self.user_employee).read(["date_from"])
        validation.action_validate()
        self.assertEqual(HrAttendanceValidationEmployee.search_count([]), 0)
        with self.assertRaisesRegex(
            AccessError, r".*doesn\'t have \'read\' access to.*"
        ):
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

    def test_hr_holidays_public(self):
        validation = self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee.id,
                "date_from": "2021-07-12",
                "date_to": "2021-07-18",
            }
        )

        self.assertEqual(validation.theoretical_hours, 40 - 8)

    def test_employee_3_no_validation(self):
        validation_sheet = self.HrAttendanceValidation.create(
            {
                "employee_id": self.employee3.id,
                "date_from": "2021-12-06",
                "date_to": "2021-12-12",
            }
        )
        validation_sheet.action_retrieve_attendance_and_leaves()
        self.assertFalse(validation_sheet.leave_ids)
        self.assertFalse(validation_sheet.attendance_ids)
        self.assertFalse(validation_sheet.attendance_due_ids)
        with self.assertRaisesRegex(
            ValidationError,
            "Can't validate weekly validation attendance sheets "
            f"for {self.employee3.name}.*",
        ):
            validation_sheet.action_validate()

    def test_employee_3_overtime(self):
        """make sure we do not create regression
        in odoo mechanisms"""
        overtimes = self.env["hr.attendance.overtime"].search(
            [("employee_id", "=", self.employee3.id), ("adjustment", "=", False)]
        )
        self.assertEqual(len(overtimes), 2)
        self.assertEqual(sum(overtimes.mapped("duration_real")), 1)

    def test_leave_requires_allocation(self):
        self.leave_type_compensatory2.requires_allocation = "yes"
        self.leave_type_compensatory2.overtime_deductible = True
        self.leave_type_compensatory2.allows_negative = False
        self.env["hr.attendance.overtime"].create(
            {
                "employee_id": self.employee3.id,
                "date": "2021-01-05",
                "duration": 16,
                "duration_real": 16,
                "adjustment": True,
            }
        )
        allocations = self.env["hr.leave.allocation"].create(
            [
                {
                    "employee_id": self.employee3.id,
                    "holiday_status_id": self.leave_type_compensatory2.id,
                    "number_of_days": 1,
                    "holiday_type": "employee",
                    "date_from": "2021-01-01",
                    "date_to": "2021-12-31",
                    "state": "confirm",
                },
            ]
        )
        allocations.filtered(
            lambda allocation: allocation.state != "validate"
        ).action_validate()
        assert all(
            allocations.mapped(lambda allocation: allocation.state == "validate")
        )

        with self.assertRaisesRegex(
            ValidationError,
            f"The employee {self.employee3.name} does not have enough "
            "extra hours to request this leave.",
        ):
            self.env["hr.leave"].create(
                {
                    "employee_id": self.employee3.id,
                    "holiday_status_id": self.leave_type_compensatory2.id,
                    # overlap two weeks
                    "request_date_from": "2021-12-13",
                    "request_date_to": "2021-12-15",
                    "number_of_days": 3,
                    "state": "draft",
                }
            )

    def test_leave_requires_minimum_allocation_raise(self):
        self.leave_type_compensatory2.requires_allocation = "yes"
        self.leave_type_compensatory2.overtime_deductible = True
        self.leave_type_compensatory2.allows_negative = True
        self.leave_type_compensatory2.max_allowed_negative = 2
        self.env["hr.attendance.overtime"].create(
            {
                "employee_id": self.employee3.id,
                "date": "2021-01-05",
                "duration": 16,
                "duration_real": 16,
                "adjustment": True,
            }
        )
        allocations = self.env["hr.leave.allocation"].create(
            [
                {
                    "employee_id": self.employee3.id,
                    "holiday_status_id": self.leave_type_compensatory2.id,
                    "number_of_days": 1,
                    "holiday_type": "employee",
                    "date_from": "2021-01-01",
                    "date_to": "2021-12-31",
                    "state": "confirm",
                },
            ]
        )
        allocations.filtered(
            lambda allocation: allocation.state != "validate"
        ).action_validate()
        assert all(
            allocations.mapped(lambda allocation: allocation.state == "validate")
        )

        with self.assertRaisesRegex(
            ValidationError,
            "You cannot request more than 2 "
            "extra hours requested 24 hours, "
            "currently 9 hours",
        ):
            self.env["hr.leave"].create(
                {
                    "employee_id": self.employee3.id,
                    "holiday_status_id": self.leave_type_compensatory2.id,
                    # overlap two weeks
                    "request_date_from": "2021-12-13",
                    "request_date_to": "2021-12-15",
                    "number_of_days": 3,
                    "state": "draft",
                }
            )

    def test_leave_requires_minimum_allocation(self):
        self.leave_type_compensatory2.requires_allocation = "yes"
        self.leave_type_compensatory2.overtime_deductible = True
        self.leave_type_compensatory2.allows_negative = True
        self.leave_type_compensatory2.max_allowed_negative = 35
        self.env["hr.attendance.overtime"].create(
            {
                "employee_id": self.employee3.id,
                "date": "2021-01-05",
                "duration": 16,
                "duration_real": 16,
                "adjustment": True,
            }
        )
        allocations = self.env["hr.leave.allocation"].create(
            [
                {
                    "employee_id": self.employee3.id,
                    "holiday_status_id": self.leave_type_compensatory2.id,
                    "number_of_days": 1,
                    "holiday_type": "employee",
                    "date_from": "2021-01-01",
                    "date_to": "2021-12-31",
                    "state": "confirm",
                },
            ]
        )
        allocations.filtered(
            lambda allocation: allocation.state != "validate"
        ).action_validate()
        assert all(
            allocations.mapped(lambda allocation: allocation.state == "validate")
        )
        leave = self.env["hr.leave"].create(
            {
                "employee_id": self.employee3.id,
                "holiday_status_id": self.leave_type_compensatory2.id,
                # overlap two weeks
                "request_date_from": "2021-12-13",
                "request_date_to": "2021-12-15",
                "number_of_days": 3,
                "state": "draft",
            }
        )
        leave.action_confirm()
        leave.action_validate()
        self.assertEqual(leave.state, "validate")

    def test_leave_type_display_name(self):
        self.assertEqual(self.leave_type_compensatory2.display_name, "Compensatory 2")
        self.assertEqual(
            self.leave_type_compensatory2.with_context(
                employee_id=self.employee3.id
            ).display_name,
            "Compensatory 2 (01:00 hours available)",
        )
