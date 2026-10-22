# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo.tests.common import TransactionCase


class BaseCommon(TransactionCase):
    """Base test class with common setup for attendance report tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test department
        cls.department = cls.env["hr.department"].create(
            {
                "name": "Test Department",
            }
        )

        # Create test job position
        cls.job_position = cls.env["hr.job"].create(
            {
                "name": "Test Job Position",
            }
        )

        # Create test manager
        cls.manager = cls.env["hr.employee"].create(
            {
                "name": "Test Manager",
                "department_id": cls.department.id,
                "job_id": cls.job_position.id,
                "identification_id": "MGR001",
            }
        )

        # Create test employees
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
