# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from psycopg2 import IntegrityError

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestTimeCreditType(TestHrAttendanceTimeCreditCommon):
    """Tests for hr.attendance.time.credit.type."""

    @mute_logger("odoo.sql_db")
    def test_code_company_unique_constraint(self):
        """Duplicate code within same company should raise."""
        with self.cr.savepoint():
            self.assertRaises(
                IntegrityError,
                self.env["hr.attendance.time.credit.type"].create,
                {
                    "name": "Duplicate",
                    "code": "travel",
                    "company_id": self.company.id,
                },
            )

    def test_code_unique_different_company(self):
        """Same code in a different company should be allowed."""
        company_2 = self.env["res.company"].create({"name": "Other Co"})
        rec = self.env["hr.attendance.time.credit.type"].create(
            {
                "name": "Travel Other",
                "code": "travel",
                "company_id": company_2.id,
            }
        )
        self.assertTrue(rec.id)
