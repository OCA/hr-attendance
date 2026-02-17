# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests import TransactionCase


class TestWizard(TransactionCase):
    def test_wizard(cls):
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True)
        )  # TODO: Is this correct?
        employee = cls.env.ref("hr.employee_admin")
        before = cls.env["hr.attendance.overtime.line"].search(
            [("employee_id", "=", employee.id)]
        )
        wizard = cls.env["hr.attendance.overtime.line.wizard"].create(
            {
                "date": date(2023, 1, 1),
                "duration": 4.2,
                "note": "Manually created",
            }
        )

        wizard.with_context(id=employee.id).action_create()  # TODO: Is this correct?
        after = cls.env["hr.attendance.overtime.line"].search(
            [("employee_id", "=", employee.id)]
        )
        overtime = after - before
        cls.assertEqual(len(overtime), 1)

        cls.assertEqual(overtime.duration, 4.2)
        cls.assertEqual(overtime.note, "Manually created")
