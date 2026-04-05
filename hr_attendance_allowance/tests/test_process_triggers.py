# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.tests.common import tagged

from .common import TestHrAttendanceAllowanceCommon


@tagged("post_install", "-at_install")
class TestProcessTriggers(TestHrAttendanceAllowanceCommon):
    """Tests for processing trigger mechanisms: force action, cron sweep,
    and rule-change cascade."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls.env["hr.attendance.allowance.rule"].create(
            {
                "name": "Trigger test rule",
                "allowance_type_id": cls.allowance_type.id,
                "company_id": cls.company.id,
                "condition_type": "domain",
                "domain": "[]",
                "minutes_type": "fixed",
                "minutes_fixed": 15,
                "sequence": 10,
            }
        )

    # -- action_process_allowances (force reprocess) --

    def test_action_process_multiple(self):
        """action_process_allowances should reprocess all records in the set."""
        now = fields.Datetime.now()
        att1 = self._create_attendance(
            fields.Datetime.subtract(now, hours=20),
            fields.Datetime.subtract(now, hours=12),
            context={"skip_allowance_recompute": True},
        )
        att2 = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            context={"skip_allowance_recompute": True},
        )
        self.assertEqual(len(att1.allowance_ids), 0)
        self.assertEqual(len(att2.allowance_ids), 0)
        (att1 | att2).action_process_allowances()
        self.assertEqual(len(att1.allowance_ids), 1)
        self.assertEqual(len(att2.allowance_ids), 1)

    def test_action_returns_true(self):
        """The action should always return True (for UI compatibility)."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = att.action_process_allowances()
        self.assertTrue(result)

    # -- Cron safety-net sweep --

    def test_cron_processes_pending_attendances(self):
        """Cron should process checked-out attendances that have no allowances."""
        now = fields.Datetime.now()
        att1 = self._create_attendance(
            fields.Datetime.subtract(now, hours=20),
            fields.Datetime.subtract(now, hours=12),
            context={"skip_allowance_recompute": True},
        )
        att2 = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            context={"skip_allowance_recompute": True},
        )
        self.env["hr.attendance"]._cron_process_allowances()
        self.assertEqual(len(att1.allowance_ids), 1)
        self.assertEqual(att1.allowance_ids.minutes, 15)
        self.assertEqual(len(att2.allowance_ids), 1)

    def test_cron_skips_skip_allowance(self):
        """Cron should not process attendances with skip_allowance=True."""
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            skip_allowance=True,
        )
        self.env["hr.attendance"]._cron_process_allowances()
        self.assertEqual(len(att.allowance_ids), 0)

    def test_cron_skips_no_checkout(self):
        """Cron should not process attendances without check_out."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8))
        self.env["hr.attendance"]._cron_process_allowances()
        self.assertEqual(len(att.allowance_ids), 0)

    def test_cron_no_rules(self):
        """Cron should gracefully handle no active rules."""
        self.rule.active = False
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            context={"skip_allowance_recompute": True},
        )
        self.env["hr.attendance"]._cron_process_allowances()
        self.assertEqual(len(att.allowance_ids), 0)

    def test_cron_record_exists(self):
        """The ir.cron record should exist after module install."""
        cron = self.env.ref(
            "hr_attendance_allowance.ir_cron_process_attendance_allowances",
            raise_if_not_found=False,
        )
        self.assertTrue(cron)
        self.assertEqual(cron.interval_type, "days")
        self.assertEqual(cron.interval_number, 1)

    # -- Rule-change cascade --

    def test_rule_write_triggers_reprocess(self):
        """Changing a rule's minutes should update existing allowance lines."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(att.allowance_ids.minutes, 15)
        self.rule.write({"minutes_fixed": 30})
        self.assertEqual(att.allowance_ids.minutes, 30)

    def test_rule_deactivate_removes_automatic_lines(self):
        """Deactivating a rule should remove its automatic lines from attendances."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(len(att.allowance_ids), 1)
        self.rule.write({"active": False})
        self.assertEqual(len(att.allowance_ids), 0)

    def test_rule_unlink_removes_automatic_lines(self):
        """Deleting a rule should remove its automatic lines from attendances."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(len(att.allowance_ids), 1)
        self.rule.unlink()
        self.assertEqual(len(att.allowance_ids), 0)

    # -- Locking --

    def test_cron_skips_locked(self):
        """Cron sweep should not reprocess locked attendances."""
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            context={"skip_allowance_recompute": True},
        )
        att.write({"allowance_locked": True})
        self.env["hr.attendance"]._cron_process_allowances()
        self.assertEqual(len(att.allowance_ids), 0)

    def test_rule_cascade_skips_locked(self):
        """Rule-change cascade should not reprocess locked attendances."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(att.allowance_ids.minutes, 15)
        att.write({"allowance_locked": True})
        self.rule.write({"minutes_fixed": 99})
        # Lines must remain at 15, not updated to 99
        self.assertEqual(att.allowance_ids.minutes, 15)
