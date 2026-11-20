# Copyright 2026 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.addons.base.tests.common import BaseCommon


class TestHrEmployee(BaseCommon):
    _test_user_groups = ("base.group_user", "hr_attendance.group_hr_attendance_own")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Test Employee", "user_id": cls._test_user.id}
        )

    def _check_action(self, action):
        # The fixed check_in range is gone, but the employee filter stays
        self.assertNotIn("check_in", [leaf[0] for leaf in action["domain"]])
        self.assertIn(("employee_id", "=", self.employee.id), action["domain"])
        # The current month is a removable filter
        self.assertTrue(action["context"]["search_default_check_in_filter"])

    def test_action_open_last_month_attendances(self):
        """The employee can remove the current month restriction."""
        self._check_action(
            self.employee.with_user(
                self._test_user
            ).action_open_last_month_attendances()
        )

    def test_action_open_last_month_attendances_public(self):
        """The public employee form opens the same action."""
        public_employee = self.env["hr.employee.public"].browse(self.employee.id)
        self._check_action(
            public_employee.with_user(
                self._test_user
            ).action_open_last_month_attendances()
        )
