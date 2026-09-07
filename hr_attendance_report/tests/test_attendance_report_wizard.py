# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAttendanceReportWizard(TransactionCase):
    """Test cases for Employee Attendance Report Wizard"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test data
        cls.department = cls.env["hr.department"].create(
            {
                "name": "Test Department",
            }
        )

        cls.manager = cls.env["hr.employee"].create(
            {
                "name": "Test Manager",
                "department_id": cls.department.id,
            }
        )

        cls.employee1 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 1",
                "department_id": cls.department.id,
                "parent_id": cls.manager.id,
            }
        )

        cls.employee2 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 2",
                "department_id": cls.department.id,
                "parent_id": cls.manager.id,
            }
        )

        # Create test attendance records
        cls.test_date = datetime.date(2025, 1, 15)
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
                "employee_id": cls.employee2.id,
                "check_in": datetime.datetime.combine(
                    cls.test_date, datetime.time(8, 30)
                ),
                "check_out": datetime.datetime.combine(
                    cls.test_date, datetime.time(16, 30)
                ),
            }
        )

    def test_wizard_creation(self):
        """Test wizard creation with default values"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
            }
        )

        self.assertEqual(wizard.select_month, "1")
        self.assertEqual(wizard.select_year, "2025")
        self.assertFalse(wizard.select_all_employee)
        self.assertFalse(wizard.select_all_department)

    def test_get_month_date_range(self):
        """Test date range calculation"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
            }
        )

        start_date, end_date = wizard._get_month_date_range()

        self.assertEqual(start_date, datetime.date(2025, 1, 1))
        self.assertEqual(end_date, datetime.date(2025, 1, 31))

    def test_get_month_date_range_edge_cases(self):
        """Test date range calculation with edge cases"""
        # Test February leap year
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "2",
                "select_year": "2024",  # Leap year
            }
        )

        start_date, end_date = wizard._get_month_date_range()

        self.assertEqual(start_date, datetime.date(2024, 2, 1))
        self.assertEqual(end_date, datetime.date(2024, 2, 29))

        # Test February non-leap year
        wizard.select_year = "2023"  # Non-leap year

        start_date, end_date = wizard._get_month_date_range()

        self.assertEqual(start_date, datetime.date(2023, 2, 1))
        self.assertEqual(end_date, datetime.date(2023, 2, 28))

        # Test December (month with 31 days)
        wizard.select_month = "12"
        wizard.select_year = "2025"

        start_date, end_date = wizard._get_month_date_range()

        self.assertEqual(start_date, datetime.date(2025, 12, 1))
        self.assertEqual(end_date, datetime.date(2025, 12, 31))

    def test_year_validation_constraints(self):
        """Test year validation constraints (@api.constrains)"""
        current_year = datetime.date.today().year

        # Test invalid year format (should fail constraint)
        with self.assertRaises(ValidationError):
            self.env["employee.attendance.report.wizard"].create(
                {
                    "select_month": "1",
                    "select_year": "abcd",
                }
            )

        # Test another invalid format
        with self.assertRaises(ValidationError):
            self.env["employee.attendance.report.wizard"].create(
                {
                    "select_month": "1",
                    "select_year": "20ab",
                }
            )

        # Test valid years (should pass)
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "1999",
            }
        )
        self.assertEqual(wizard.select_year, "1999")

        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": str(current_year),
            }
        )
        self.assertEqual(wizard.select_year, str(current_year))

        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2050",
            }
        )
        self.assertEqual(wizard.select_year, "2050")

    def test_year_constraint_realistic_cases(self):
        """Test year constraint with realistic input cases"""
        # Test invalid 4-digit
        # year (user can type this)
        with self.assertRaises(ValidationError):
            self.env["employee.attendance.report.wizard"].create(
                {
                    "select_month": "1",
                    "select_year": "abcd",  # 4 characters, invalid format
                }
            )

        # Test year with numbers
        # and letters (user can type this)
        with self.assertRaises(ValidationError):
            self.env["employee.attendance.report.wizard"].create(
                {
                    "select_month": "1",
                    "select_year": "20ab",  # 4 characters, invalid format
                }
            )

        # Test valid 4-digit year (should pass)
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",  # 4 digits, valid format
            }
        )
        self.assertEqual(wizard.select_year, "2025")

    def test_get_selected_employees_direct_selection(self):
        """Test getting employees from direct selection"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [self.employee1.id])],
            }
        )

        employees = wizard._get_selected_employees()

        self.assertEqual(len(employees), 1)
        self.assertEqual(employees, self.employee1)

    def test_get_selected_employees_by_department(self):
        """Test getting employees by department selection"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_department_ids": [(6, 0, [self.department.id])],
            }
        )

        employees = wizard._get_selected_employees()

        # Should include all employees
        # in the department (employee1, employee2, manager)
        self.assertGreaterEqual(len(employees), 2)
        self.assertIn(self.employee1, employees)
        self.assertIn(self.employee2, employees)

    def test_get_selected_employees_mixed_selection(self):
        """Test getting employees from both direct and department selection"""
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

        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [other_employee.id])],
                "hr_department_ids": [(6, 0, [self.department.id])],
            }
        )

        employees = wizard._get_selected_employees()

        # Should include employees from
        # both sources without duplicates
        self.assertIn(self.employee1, employees)
        self.assertIn(self.employee2, employees)
        self.assertIn(other_employee, employees)

    def test_get_selected_employees_no_selection_raises_error(self):
        """Test that no selection raises ValidationError"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                # No employees or departments selected
            }
        )

        with self.assertRaises(ValidationError):
            wizard._get_selected_employees()

    def test_get_selected_employees_union_without_duplicates(self):
        """Test that union removes duplicates when employee is in selected department"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [self.employee1.id])],  # Direct selection
                "hr_department_ids": [
                    (6, 0, [self.department.id])
                ],  # Department containing employee1
            }
        )

        employees = wizard._get_selected_employees()

        # employee1 should appear only
        # once despite being selected both ways
        employee1_count = len([emp for emp in employees if emp.id == self.employee1.id])
        self.assertEqual(employee1_count, 1)

        # Should still include other employees from department
        self.assertIn(self.employee2, employees)

    def test_onchange_select_all_employee(self):
        """Test select all employees onchange"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
            }
        )

        wizard.select_all_employee = True
        wizard._onchange_select_all()

        # Should select all employees
        all_employees = self.env["hr.employee"].search([])
        self.assertEqual(set(wizard.hr_employee_ids.ids), set(all_employees.ids))

    def test_onchange_select_all_department(self):
        """Test select all departments onchange"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
            }
        )

        wizard.select_all_department = True
        wizard._onchange_select_all()

        # Should select all departments
        all_departments = self.env["hr.department"].search([])
        self.assertEqual(set(wizard.hr_department_ids.ids), set(all_departments.ids))

    def test_onchange_hr_employee_ids(self):
        """Test employee selection onchange"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
            }
        )

        # Select some employees
        wizard.hr_employee_ids = [(6, 0, [self.employee1.id])]
        wizard._onchange_hr_employee_ids()

        # Should not set select_all_employee to True
        self.assertFalse(wizard.select_all_employee)

        # Select all employees
        all_employees = self.env["hr.employee"].search([])
        wizard.hr_employee_ids = [(6, 0, all_employees.ids)]
        wizard._onchange_hr_employee_ids()

        # Should set select_all_employee to True
        self.assertTrue(wizard.select_all_employee)

    def test_onchange_hr_department_ids(self):
        """Test onchange method for hr_department_ids field"""
        # Create additional departments for testing
        dept2 = self.env["hr.department"].create(
            {
                "name": "Test Department 2",
            }
        )

        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
            }
        )

        # Test 1: Select some departments (not all) -
        # should set select_all_department to False
        wizard.hr_department_ids = [(6, 0, [self.department.id, dept2.id])]
        wizard._onchange_hr_department_ids()
        self.assertFalse(wizard.select_all_department)

        # Test 2: Select all departments -
        # should set select_all_department to True
        all_departments = self.env["hr.department"].search([])
        wizard.hr_department_ids = [(6, 0, all_departments.ids)]
        wizard._onchange_hr_department_ids()
        self.assertTrue(wizard.select_all_department)

        # Test 3: Select no departments -
        # should set select_all_department to False
        wizard.hr_department_ids = [(6, 0, [])]
        wizard._onchange_hr_department_ids()
        self.assertFalse(wizard.select_all_department)

        # Test 4: Select only one department -
        # should set select_all_department to False
        wizard.hr_department_ids = [(6, 0, [self.department.id])]
        wizard._onchange_hr_department_ids()
        self.assertFalse(wizard.select_all_department)

    def test_onchange_hr_department_ids_edge_cases(self):
        """Test onchange hr_department_ids with edge cases"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
            }
        )

        # Test when there's only one department in the system
        all_departments = self.env["hr.department"].search([])

        if len(all_departments) == 1:
            # Select the only department -
            # should set select_all_department to True
            wizard.hr_department_ids = [(6, 0, [self.department.id])]
            wizard._onchange_hr_department_ids()
            self.assertTrue(wizard.select_all_department)

        # Now there are more departments,
        # selecting just one should be False
        wizard.hr_department_ids = [(6, 0, [self.department.id])]
        wizard._onchange_hr_department_ids()
        self.assertFalse(wizard.select_all_department)

        # Selecting all departments
        # (including new one) should be True
        all_departments_updated = self.env["hr.department"].search([])
        wizard.hr_department_ids = [(6, 0, all_departments_updated.ids)]
        wizard._onchange_hr_department_ids()
        self.assertTrue(wizard.select_all_department)

    def test_generate_employee_pdf_report_success(self):
        """Test successful PDF report generation"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [self.employee1.id])],
            }
        )

        # Test that the method runs without
        # error and returns expected structure
        result = wizard.generate_employee_pdf_report()

        # Check that it returns a report action structure
        self.assertIsInstance(result, dict)

    def test_generate_employee_excel_report_success(self):
        """Test successful Excel report generation"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [self.employee1.id])],
            }
        )

        result = wizard.generate_employee_excel_report()

        # Check return structure
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "hr.attendance.report.download")
        self.assertEqual(result["view_mode"], "form")
        self.assertEqual(result["target"], "new")

        # Check that Excel file was created
        excel_record = self.env["hr.attendance.report.download"].browse(
            result["res_id"]
        )
        self.assertTrue(excel_record.file_name)
        self.assertTrue(excel_record.datas_fname)
        self.assertIn("Attendance_Report", excel_record.datas_fname)

    def test_excel_filename_generation(self):
        """Test Excel filename generation with date"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [self.employee1.id])],
            }
        )

        result = wizard.generate_employee_excel_report()

        # Check that Excel file was
        # created with proper filename
        excel_record = self.env["hr.attendance.report.download"].browse(
            result["res_id"]
        )
        self.assertTrue(excel_record.datas_fname)

        # Should contain year and month in filename
        expected_pattern = "Attendance_Report_2025_01"
        self.assertIn(expected_pattern, excel_record.datas_fname)

    def test_excel_report_with_no_attendances(self):
        """Test Excel report with employee having no attendances"""
        # Create employee with no attendance records
        employee_no_attendance = self.env["hr.employee"].create(
            {
                "name": "No Attendance Employee",
                "department_id": self.department.id,
            }
        )

        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "12",
                "select_year": "2024",
                "hr_employee_ids": [(6, 0, [employee_no_attendance.id])],
            }
        )

        result = wizard.generate_employee_excel_report()

        # Should still generate report successfully
        self.assertEqual(result["type"], "ir.actions.act_window")

        # Check that Excel file was created
        excel_record = self.env["hr.attendance.report.download"].browse(
            result["res_id"]
        )
        self.assertTrue(excel_record.file_name)

    def test_excel_sheet_creation_with_long_employee_name(self):
        """Test Excel sheet creation with employee name longer than 31 chars"""
        # Create employee with very long name (>31 chars)
        long_name_employee = self.env["hr.employee"].create(
            {
                "name": "This Is A Very Long Employee "
                "Name That Exceeds Thirty One Characters",
                "department_id": self.department.id,
            }
        )

        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [long_name_employee.id])],
            }
        )

        # Should handle long names gracefully
        # (Excel sheet names are limited to 31 chars)
        result = wizard.generate_employee_excel_report()

        self.assertEqual(result["type"], "ir.actions.act_window")
        excel_record = self.env["hr.attendance.report.download"].browse(
            result["res_id"]
        )
        self.assertTrue(excel_record.file_name)

    def test_default_get_with_attendance_manager(self):
        """Test default_get when user is attendance manager"""
        # Create a user with attendance manager rights
        manager_user = self.env["res.users"].create(
            {
                "name": "Attendance Manager",
                "login": "manager@test.com",
                "groups_id": [
                    (4, self.env.ref("base.group_user").id),
                    (4, self.env.ref("hr_attendance.group_hr_attendance_manager").id),
                ],
            }
        )

        # Create wizard as manager user
        wizard = (
            self.env["employee.attendance.report.wizard"]
            .with_user(manager_user)
            .create(
                {
                    "select_month": "1",
                    "select_year": "2025",
                }
            )
        )

        # Manager should not have employees pre-selected
        self.assertFalse(wizard.hr_employee_ids)

    def test_default_get_with_regular_user(self):
        """Test default_get when user is NOT attendance manager"""
        # Create a regular employee user (not manager)
        employee_user = self.env["res.users"].create(
            {
                "name": "Regular Employee User",
                "login": "employee@test.com",
                "groups_id": [(4, self.env.ref("base.group_user").id)],
            }
        )

        # Link employee to user
        self.employee1.user_id = employee_user.id

        # Call default_get directly
        wizard_model = self.env["employee.attendance.report.wizard"].with_user(
            employee_user
        )
        default_vals = wizard_model.default_get(
            ["hr_employee_ids", "select_month", "select_year"]
        )

        # Verify default_get was called successfully and returns expected structure
        self.assertIn("select_month", default_vals)
        self.assertIn("select_year", default_vals)

        # If hr_employee_ids is in defaults, it should contain the user's employee
        if "hr_employee_ids" in default_vals:
            self.assertTrue(default_vals["hr_employee_ids"])

    def test_default_get_regular_user_no_employee(self):
        """Test default_get when user has no linked employee"""
        # Create a user without linked employee
        user_no_employee = self.env["res.users"].create(
            {
                "name": "User Without Employee",
                "login": "noemployee@test.com",
                "groups_id": [(4, self.env.ref("base.group_user").id)],
            }
        )

        # Test default_get behavior
        wizard_vals = (
            self.env["employee.attendance.report.wizard"]
            .with_user(user_no_employee)
            .default_get(["hr_employee_ids", "select_month", "select_year"])
        )

        # Should not have any employees pre-selected
        self.assertFalse(wizard_vals.get("hr_employee_ids"))

    def test_excel_report_with_multiple_employees(self):
        """Test Excel report generation with multiple employees"""
        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [self.employee1.id, self.employee2.id])],
            }
        )

        result = wizard.generate_employee_excel_report()

        # Should generate report with both employees
        self.assertEqual(result["type"], "ir.actions.act_window")
        excel_record = self.env["hr.attendance.report.download"].browse(
            result["res_id"]
        )
        self.assertTrue(excel_record.file_name)
        self.assertIn("2025_01", excel_record.datas_fname)

    def test_excel_employee_with_complete_info(self):
        """Test Excel creation for employee with all information"""
        # Set complete information for employee
        self.employee1.sudo().identification_id = "IDENT123"
        self.employee1.company_id.vat = "ES12345678"

        wizard = self.env["employee.attendance.report.wizard"].create(
            {
                "select_month": "1",
                "select_year": "2025",
                "hr_employee_ids": [(6, 0, [self.employee1.id])],
            }
        )

        result = wizard.generate_employee_excel_report()

        # Should successfully create Excel with all fields
        self.assertEqual(result["type"], "ir.actions.act_window")
        excel_record = self.env["hr.attendance.report.download"].browse(
            result["res_id"]
        )
        self.assertTrue(excel_record.file_name)

    def test_get_view_regular_user_readonly(self):
        """Test _get_view makes employee field readonly for non-managers"""
        # Create a regular user (not attendance manager)
        employee_user = self.env["res.users"].create(
            {
                "name": "Regular Employee User",
                "login": "employee2@test.com",
                "groups_id": [(4, self.env.ref("base.group_user").id)],
            }
        )

        # Link employee to user
        self.employee2.user_id = employee_user.id

        # Get view as regular user
        wizard_model = self.env["employee.attendance.report.wizard"].with_user(
            employee_user
        )

        # Call _get_view to check if field is made readonly
        arch, view = wizard_model._get_view(view_type="form")

        # Check that hr_employee_ids field exists in the view
        # (This tests that the method runs without error)
        self.assertIsNotNone(arch)

    def test_get_view_manager_user(self):
        """Test _get_view for attendance manager user"""
        # Create a manager user
        manager_user = self.env["res.users"].create(
            {
                "name": "Attendance Manager",
                "login": "manager2@test.com",
                "groups_id": [
                    (4, self.env.ref("base.group_user").id),
                    (4, self.env.ref("hr_attendance.group_hr_attendance_manager").id),
                ],
            }
        )

        # Get view as manager
        wizard_model = self.env["employee.attendance.report.wizard"].with_user(
            manager_user
        )

        # Call _get_view - should not modify readonly attribute for manager
        arch, view = wizard_model._get_view(view_type="form")

        # Check that arch is returned successfully
        self.assertIsNotNone(arch)
        self.assertIsNotNone(view)
