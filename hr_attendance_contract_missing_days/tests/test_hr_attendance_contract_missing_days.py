from odoo.addons.hr_attendance_missing_days.tests import test_attendance


class TestAttendance(test_attendance.TestAttendance):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.contract = cls.env["hr.contract"].create(
            {
                "name": "2023",
                "date_start": "2023-01-01",
                "date_end": "2023-12-31",
                "state": "open",
                "wage": 42,
                "employee_id": cls.employee.id,
            }
        )

    def _clone_employee(self, employee, defaults):
        result = super()._clone_employee(employee, defaults)
        for contract in employee.contract_ids:
            contract.copy({"employee_id": result.id, "state": "open"})
        return result
