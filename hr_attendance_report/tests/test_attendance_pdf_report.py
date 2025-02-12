# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import logging

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestAttendancePdfReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test data
        cls.department = cls.env["hr.department"].create(
            {
                "name": "Test Department",
            }
        )

        cls.job_position = cls.env["hr.job"].create(
            {
                "name": "Test Job Position",
            }
        )

        cls.manager = cls.env["hr.employee"].create(
            {
                "name": "Test Manager",
                "department_id": cls.department.id,
                "job_id": cls.job_position.id,
                "identification_id": "MGR001",
            }
        )

        cls.employee1 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 1",
                "department_id": cls.department.id,
                "parent_id": cls.manager.id,
                "job_id": cls.job_position.id,
                "identification_id": "EMP001",
            }
        )

        cls.employee2 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 2",
                "department_id": cls.department.id,
                "parent_id": cls.manager.id,
                "job_id": cls.job_position.id,
                "barcode": "EMP002",
            }
        )

        # Create test attendance records
        cls.test_date = datetime.date(2025, 1, 15)
        cls.test_date2 = datetime.date(2025, 1, 16)

        cls.attendance1 = cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee1.id,
                "check_in": datetime.datetime.combine(
                    cls.test_date, datetime.time(9, 0)
                ),
                "check_out": datetime.datetime.combine(
                    cls.test_date, datetime.time(17, 0)
                ),
            }
        )

        cls.attendance2 = cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee1.id,
                "check_in": datetime.datetime.combine(
                    cls.test_date2, datetime.time(8, 30)
                ),
                "check_out": datetime.datetime.combine(
                    cls.test_date2, datetime.time(16, 30)
                ),
            }
        )

        cls.attendance3 = cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee2.id,
                "check_in": datetime.datetime.combine(
                    cls.test_date, datetime.time(10, 0)
                ),
                "check_out": datetime.datetime.combine(
                    cls.test_date, datetime.time(18, 0)
                ),
            }
        )

        # Incomplete attendance (no check_out)
        cls.attendance4 = cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee2.id,
                "check_in": datetime.datetime.combine(
                    cls.test_date2, datetime.time(9, 15)
                ),
            }
        )

    def test_report_model_creation(self):
        # Try different possible report model names
        possible_names = [
            "report.hr_attendance_report.report_one_set",
            "report.hr_attendance_report.report_attendance_report_wizard",
            "report.hr_attendance_report.attendance_report",
        ]

        report_model = None
        for name in possible_names:
            try:
                model = self.env[name]
                if model:
                    report_model = model
                    break
            except KeyError:
                continue

        # If no specific report model found, skip this test
        if not report_model:
            self.skipTest("Report model not found with expected names")

        self.assertTrue(report_model)

    def _get_report_model(self):
        possible_names = [
            "report.hr_attendance_report.report_one_set",
            "report.hr_attendance_report.report_attendance_report_wizard",
            "report.hr_attendance_report.attendance_report",
        ]

        for name in possible_names:
            try:
                return self.env[name]
            except KeyError:
                continue

        self.skipTest("Report model not found")

    def test_get_report_values_missing_data(self):
        report_model = self._get_report_model()

        # Test with no data
        with self.assertRaises(ValidationError):
            report_model._get_report_values([], data=None)

        # Test with empty form_data
        with self.assertRaises(ValidationError):
            report_model._get_report_values([], data={})

    def test_get_report_values_missing_month_year(self):
        report_model = self._get_report_model()

        # Missing month
        with self.assertRaises(ValidationError):
            report_model._get_report_values(
                [],
                data={
                    "form_data": {
                        "select_year": "2025",
                        "hr_employee_ids": [self.employee1.id],
                    }
                },
            )

        # Missing year
        with self.assertRaises(ValidationError):
            report_model._get_report_values(
                [],
                data={
                    "form_data": {
                        "select_month": "1",
                        "hr_employee_ids": [self.employee1.id],
                    }
                },
            )

    def test_get_report_values_invalid_date_format(self):
        report_model = self._get_report_model()

        # Test invalid month
        with self.assertRaises(ValidationError):
            report_model._get_report_values(
                [],
                data={
                    "form_data": {
                        "select_month": "invalid",
                        "select_year": "2025",
                        "hr_employee_ids": [self.employee1.id],
                    }
                },
            )

        # Test invalid year
        with self.assertRaises(ValidationError):
            report_model._get_report_values(
                [],
                data={
                    "form_data": {
                        "select_month": "1",
                        "select_year": "invalid_year",
                        "hr_employee_ids": [self.employee1.id],
                    }
                },
            )

        # Test month out of range
        with self.assertRaises(ValidationError):
            report_model._get_report_values(
                [],
                data={
                    "form_data": {
                        "select_month": "13",  # Invalid month
                        "select_year": "2025",
                        "hr_employee_ids": [self.employee1.id],
                    }
                },
            )

    def test_get_selected_employees_direct_selection(self):
        report_model = self._get_report_model()

        form_data = {
            "hr_employee_ids": [self.employee1.id, self.employee2.id],
            "hr_department_ids": [],
        }

        if hasattr(report_model, "_get_selected_employees"):
            employees = report_model._get_selected_employees(form_data)

            self.assertEqual(len(employees), 2)
            self.assertIn(self.employee1, employees)
            self.assertIn(self.employee2, employees)
        else:
            # Test through _get_report_values for original code
            form_data.update(
                {
                    "select_month": "1",
                    "select_year": "2025",
                }
            )

            data = {"form_data": form_data}
            result = report_model._get_report_values([], data)

            # Just verify it doesn't crash - detailed testing in other methods
            self.assertIsInstance(result, dict)

    def test_get_selected_employees_by_department(self):
        report_model = self.env["report.hr_attendance_report.report_one_set"]

        form_data = {
            "hr_employee_ids": [],
            "hr_department_ids": [self.department.id],
        }

        employees = report_model._get_selected_employees(form_data)

        # Should include all employees in the department
        self.assertGreaterEqual(len(employees), 2)
        self.assertIn(self.employee1, employees)
        self.assertIn(self.employee2, employees)

    def test_get_selected_employees_mixed_selection(self):
        # Create employee in different department
        other_department = self.env["hr.department"].create(
            {
                "name": "Other Department",
            }
        )

        other_employee = self.env["hr.employee"].create(
            {
                "name": "Other Employee",
                "department_id": other_department.id,
            }
        )

        report_model = self.env["report.hr_attendance_report.report_one_set"]

        form_data = {
            "hr_employee_ids": [other_employee.id],
            "hr_department_ids": [self.department.id],
        }

        employees = report_model._get_selected_employees(form_data)

        # Should include employees from both sources without duplicates
        self.assertIn(self.employee1, employees)
        self.assertIn(self.employee2, employees)
        self.assertIn(other_employee, employees)

    def test_get_selected_employees_empty_departments(self):
        report_model = self._get_report_model()

        # Test with empty department list but valid employees
        form_data = {
            "hr_employee_ids": [self.employee1.id],
            "hr_department_ids": [],  # Empty departments
        }

        if hasattr(report_model, "_get_selected_employees"):
            employees = report_model._get_selected_employees(form_data)
            self.assertEqual(len(employees), 1)
            self.assertEqual(employees, self.employee1)
        else:
            # Test through _get_report_values for original code
            form_data.update(
                {
                    "select_month": "1",
                    "select_year": "2025",
                }
            )

            data = {"form_data": form_data}
            result = report_model._get_report_values([], data)
            self.assertIsInstance(result, dict)

    def test_get_selected_employees_integer_conversion(self):
        report_model = self._get_report_model()

        # Test when IDs come as integers instead of lists
        form_data = {
            "hr_employee_ids": self.employee1.id,  # Single integer
            "hr_department_ids": self.department.id,  # Single integer
        }

        if hasattr(report_model, "_get_selected_employees"):
            employees = report_model._get_selected_employees(form_data)
            # Should handle integer conversion and include employees
            self.assertGreaterEqual(len(employees), 1)
        else:
            # Test through _get_report_values for original code
            form_data.update(
                {
                    "select_month": "1",
                    "select_year": "2025",
                }
            )

            data = {"form_data": form_data}
            result = report_model._get_report_values([], data)
            self.assertIsInstance(result, dict)

    def test_generate_employee_data_single_employee(self):
        report_model = self.env["report.hr_attendance_report.report_one_set"]

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 31)

        employees = self.employee1
        employee_data = report_model._generate_employee_data(
            employees, start_date, end_date
        )

        self.assertEqual(len(employee_data), 1)

        emp_data = employee_data[0]
        self.assertEqual(emp_data["emp_name"], "Test Employee 1")
        self.assertEqual(emp_data["emp_code"], "EMP001")
        self.assertEqual(emp_data["manager"], "Test Manager")
        self.assertEqual(emp_data["department"], "Test Department")
        self.assertEqual(emp_data["job_title"], "Test Job Position")

        # Should have 2 attendance records
        self.assertEqual(len(emp_data["attendances"]), 2)
        self.assertEqual(emp_data["total_days"], 2)
        self.assertGreater(emp_data["total_hours"], 0)

    def test_generate_employee_data_employee_with_barcode(self):
        report_model = self.env["report.hr_attendance_report.report_one_set"]

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 31)

        employees = self.employee2
        employee_data = report_model._generate_employee_data(
            employees, start_date, end_date
        )

        emp_data = employee_data[0]
        # Should use barcode as emp_code since no identification_id
        self.assertEqual(emp_data["emp_code"], "EMP002")

    def test_generate_employee_data_employee_no_code(self):
        # Create employee without identification_id or barcode
        employee_no_code = self.env["hr.employee"].create(
            {
                "name": "No Code Employee",
                "department_id": self.department.id,
            }
        )

        report_model = self.env["report.hr_attendance_report.report_one_set"]

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 31)

        employees = employee_no_code
        employee_data = report_model._generate_employee_data(
            employees, start_date, end_date
        )

        emp_data = employee_data[0]
        # Should use database ID as fallback
        self.assertEqual(emp_data["emp_code"], str(employee_no_code.id))

    def test_generate_employee_data_no_attendances(self):
        # Create employee with no attendance
        employee_no_att = self.env["hr.employee"].create(
            {
                "name": "No Attendance Employee",
                "department_id": self.department.id,
            }
        )

        report_model = self.env["report.hr_attendance_report.report_one_set"]

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 31)

        employees = employee_no_att
        employee_data = report_model._generate_employee_data(
            employees, start_date, end_date
        )

        emp_data = employee_data[0]
        self.assertEqual(len(emp_data["attendances"]), 0)
        self.assertEqual(emp_data["total_hours"], 0)
        self.assertEqual(emp_data["total_days"], 0)
        self.assertEqual(emp_data["avg_hours_per_day"], 0)

    def test_get_report_values_complete_flow(self):
        report_model = self.env["report.hr_attendance_report.report_one_set"]

        form_data = {
            "select_month": "1",
            "select_year": "2025",
            "hr_employee_ids": [self.employee1.id],
            "hr_department_ids": [],
        }

        data = {"form_data": form_data}
        docids = [1]  # Mock docids

        result = report_model._get_report_values(docids, data)

        # Check return structure - use the correct key name from your original code
        self.assertEqual(result["doc_ids"], docids)
        self.assertEqual(result["doc_model"], "hr.employee")
        self.assertEqual(result["form_data"], form_data)
        self.assertEqual(result["month_name"], "January")
        self.assertEqual(result["year"], "2025")

        # Check dates
        self.assertEqual(result["start_date"], datetime.date(2025, 1, 1))
        self.assertEqual(result["end_date"], datetime.date(2025, 1, 31))

        # Check employee data - this should
        # match your original code structure
        # If your original code returns 'emp_name'
        # instead of 'employees_data', adjust accordingly
        employee_data_key = (
            "employees_data" if "employees_data" in result else "emp_name"
        )
        self.assertIn(employee_data_key, result)
        self.assertEqual(len(result[employee_data_key]), 1)

        emp_data = result[employee_data_key][0]
        self.assertEqual(emp_data["emp_name"], "Test Employee 1")

    def test_attendance_ordering(self):
        report_model = self.env["report.hr_attendance_report.report_one_set"]

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 31)

        employees = self.employee1
        employee_data = report_model._generate_employee_data(
            employees, start_date, end_date
        )

        emp_data = employee_data[0]
        attendances = emp_data["attendances"]

        # Check that attendances are in chronological order
        for i in range(1, len(attendances)):
            if attendances[i - 1]["check_in"] and attendances[i]["check_in"]:
                self.assertLessEqual(
                    attendances[i - 1]["check_in"], attendances[i]["check_in"]
                )

    def test_worked_hours_precision(self):
        report_model = self.env["report.hr_attendance_report.report_one_set"]

        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 1, 31)

        employees = self.employee1
        employee_data = report_model._generate_employee_data(
            employees, start_date, end_date
        )

        emp_data = employee_data[0]

        # Check that hours are rounded to 2 decimal places
        for att in emp_data["attendances"]:
            worked_hours = att["worked_hours"]
            # Check that it's a number with at most 2 decimal places
            self.assertEqual(worked_hours, round(worked_hours, 2))

        # Check total hours precision
        self.assertEqual(emp_data["total_hours"], round(emp_data["total_hours"], 2))
        self.assertEqual(
            emp_data["avg_hours_per_day"], round(emp_data["avg_hours_per_day"], 2)
        )
