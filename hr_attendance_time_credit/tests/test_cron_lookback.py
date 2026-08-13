# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Tests for the cron lookback window."""


from odoo import fields
from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestCronLookback(TestHrAttendanceTimeCreditCommon):
    """Tests for cron lookback window via ir.config_parameter."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls._make_rule("Lookback Rule", minutes_fixed=15)
        cls.param_model = cls.env["ir.config_parameter"].sudo()

    def _set_lookback(self, days):
        self.param_model.set_param(
            "hr_attendance_time_credit.cron_lookback_days", str(days)
        )

    def _remove_lookback_param(self):
        self.param_model.set_param("hr_attendance_time_credit.cron_lookback_days", "")

    def _old_attendance(self, days_ago):
        now = fields.Datetime.now().replace(hour=8, minute=0, second=0)
        check_in = fields.Datetime.subtract(now, days=days_ago)
        check_out = fields.Datetime.add(check_in, hours=8)
        return self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": check_in,
                "check_out": check_out,
            }
        )

    def _assert_lookback(self, days_ago, lookback, expected):
        if lookback is not None:
            self._set_lookback(lookback)
        att = self._old_attendance(days_ago)
        att.time_credit_ids.filtered(lambda c: c.origin == "automatic").unlink()
        self.env["hr.attendance"]._cron_process_time_credits()
        att.invalidate_recordset(["time_credit_ids"])
        credit_lines = att.time_credit_ids.filtered(
            lambda c: c.origin == "automatic" and c.type_id == self.credit_type
        )
        self.assertEqual(len(credit_lines), expected)

    def test_attendance_within_lookback_processed(self):
        """Attendance within lookback window is processed by cron."""
        self._assert_lookback(10, 90, 1)

    def test_attendance_outside_lookback_skipped(self):
        """Attendance outside lookback window is skipped by cron."""
        self._assert_lookback(120, 90, 0)

    def test_lookback_zero_means_no_cutoff(self):
        """System param set to 0 means no cutoff — full sweep."""
        self._assert_lookback(120, 0, 1)

    def test_lookback_default_when_param_absent(self):
        """When param is absent, default 90 days is used."""
        self._remove_lookback_param()
        self._assert_lookback(10, None, 1)
        self._assert_lookback(120, None, 0)
