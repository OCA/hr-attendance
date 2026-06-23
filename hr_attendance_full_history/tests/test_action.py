# Copyright 2026 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.addons.base.tests.common import BaseCommon


class TestResUsers(BaseCommon):
    def test_action_open_last_month_attendances(self):
        """Check that the action is modified as expected."""
        action = self.env.user.action_open_last_month_attendances()
        # Check that the hard domain for check_in is NOT there
        for domain_item in action["domain"]:
            self.assertNotEqual(
                domain_item[:2],
                ("check_in", ">="),
                "Domain for 'check_in' should not exist",
            )
        # The context now contains the search default
        self.assertTrue(action["context"]["search_default_filter_this_month"])
