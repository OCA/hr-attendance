# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests import TransactionCase


class TestWizard(TransactionCase):
    def test_wizard(self):
        employee = self.env.ref("hr.employee_admin")
        before = self.env["hr.attendance.overtime"].search(
            [("employee_id", "=", employee.id)]
        )
        wizard = self.env["hr.attendance.overtime.wizard"].create(
            {
                "date": date(2023, 1, 1),
                "duration": 4.2,
                "note": "Manually created",
            }
        )

        wizard.with_context(active_id=employee.id).action_create()
        after = self.env["hr.attendance.overtime"].search(
            [("employee_id", "=", employee.id)]
        )
        overtime = after - before
        self.assertEqual(len(overtime), 1)

        self.assertEqual(overtime.duration, 4.2)
        self.assertEqual(overtime.note, "Manually created")
