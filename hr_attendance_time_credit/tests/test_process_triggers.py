# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import datetime

from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestProcessTriggers(TestHrAttendanceTimeCreditCommon):
    """Tests for processing trigger mechanisms: force action, cron sweep,
    and rule-change cascade."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls._make_rule("Trigger test rule", minutes_fixed=15)

    def test_action_process_multiple(self):
        """action_process_time_credits should reprocess all records in the set."""
        att1 = self._create_attendance(
            datetime(2026, 1, 10, 7, 0, 0),
            datetime(2026, 1, 10, 8, 0, 0),
            context={"skip_time_credit_recompute": True},
        )
        att2 = self._create_attendance(
            datetime(2026, 1, 10, 9, 0, 0),
            datetime(2026, 1, 10, 17, 0, 0),
            context={"skip_time_credit_recompute": True},
        )
        self.assertEqual(len(att1.time_credit_ids), 0)
        self.assertEqual(len(att2.time_credit_ids), 0)
        result = (att1 | att2).action_process_time_credits()
        self.assertTrue(result)
        self.assertEqual(len(att1.time_credit_ids), 1)
        self.assertEqual(len(att2.time_credit_ids), 1)

    # -- Cron safety-net sweep --

    def test_cron_skips_skip_time_credit(self):
        """Cron should not process attendances with skip_time_credit=True."""
        att = self._create_fixed_attendance(
            hours=8, check_in_hour=8, skip_time_credit=True
        )
        self.env["hr.attendance"]._cron_process_time_credits()
        self.assertEqual(len(att.time_credit_ids), 0)

    def test_cron_no_rules(self):
        """Cron should gracefully handle no active rules."""
        self.rule.active = False
        att = self._create_fixed_attendance(
            hours=8,
            check_in_hour=8,
            context={"skip_time_credit_recompute": True},
        )
        self.env["hr.attendance"]._cron_process_time_credits()
        self.assertEqual(len(att.time_credit_ids), 0)

    def test_cron_record_exists(self):
        """The ir.cron record should exist after module install."""
        cron = self.env.ref(
            "hr_attendance_time_credit.ir_cron_process_attendance_time_credits",
            raise_if_not_found=False,
        )
        self.assertTrue(cron)
        self.assertEqual(cron.interval_type, "days")
        self.assertEqual(cron.interval_number, 1)

    # -- Rule-change cascade --

    def test_rule_write_triggers_reprocess(self):
        """Changing a rule's minutes should update existing credit lines."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.assertEqual(att.time_credit_ids.minutes, 15)
        self.rule.write({"minutes_fixed": 30})
        att.invalidate_recordset(["time_credit_ids"])
        self.assertEqual(att.time_credit_ids.minutes, 30)

    def test_rule_deactivate_removes_automatic_lines(self):
        """Deactivating a rule should remove its automatic lines from attendances."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.assertEqual(len(att.time_credit_ids), 1)
        self.rule.write({"active": False})
        self.assertEqual(len(att.time_credit_ids), 0)

    def test_rule_write_without_recompute_trigger(self):
        """Writing a non-trigger field on a rule does not cascade."""
        rule = self._make_rule("Write no trigger", minutes_fixed=10)
        rule.write({"name": "Write no trigger renamed"})
        self.assertEqual(rule.name, "Write no trigger renamed")

    def test_rule_write_trigger_no_attendances(self):
        """Writing a trigger field for a company with no attendances is a no-op."""
        empty_company = self.env["res.company"].create({"name": "No Attendances Co"})
        rule = self._make_rule(
            "Trigger no attendances", minutes_fixed=10, company_id=empty_company.id
        )
        rule.write({"minutes_fixed": 20})
        self.assertEqual(rule.minutes_fixed, 20)

    # -- Locking --

    def test_cron_skips_locked(self):
        """Cron sweep should not reprocess locked attendances."""
        att = self._create_fixed_attendance(
            hours=8,
            check_in_hour=8,
            context={"skip_time_credit_recompute": True},
        )
        att.write({"credit_locked": True})
        self.env["hr.attendance"]._cron_process_time_credits()
        self.assertEqual(len(att.time_credit_ids), 0)

    def test_rule_cascade_skips_locked(self):
        """Rule-change cascade should not reprocess locked attendances."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.assertEqual(att.time_credit_ids.minutes, 15)
        att.write({"credit_locked": True})
        self.rule.write({"minutes_fixed": 99})
        # Lines must remain at 15, not updated to 99
        self.assertEqual(att.time_credit_ids.minutes, 15)
