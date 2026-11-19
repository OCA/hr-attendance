# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import datetime, timedelta

from odoo.tests.common import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestHrAttendanceTimeCreditCommon(BaseCommon):
    """Shared setUp for all attendance time credit tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Test Employee", "company_id": cls.company.id}
        )
        # UTC timezone + 24/7 calendar for deterministic midnight behavior
        cls.employee.tz = "UTC"
        cls.calendar_utc = cls.env["resource.calendar"].create(
            {
                "name": "UTC 24/7",
                "company_id": cls.company.id,
                "tz": "UTC",
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": f"Day {wd}",
                            "dayofweek": str(wd),
                            "hour_from": 0,
                            "hour_to": 24,
                        },
                    )
                    for wd in range(7)
                ],
            }
        )
        cls.employee.resource_calendar_id = cls.calendar_utc
        # Credit types default to consolidate for test determinism;
        # segment_mode tests create their own types with explicit modes.
        cls.credit_type = cls.env["hr.attendance.time.credit.type"].create(
            {
                "name": "Travel Time",
                "code": "travel",
                "company_id": cls.company.id,
                "segment_mode": "consolidate",
            }
        )
        cls.credit_type_2 = cls.env["hr.attendance.time.credit.type"].create(
            {
                "name": "Dressing Time",
                "code": "dressing",
                "company_id": cls.company.id,
                "segment_mode": "consolidate",
            }
        )
        cls.hr_attendance_model_id = cls.env["ir.model"]._get_id("hr.attendance")

    @classmethod
    def _create_attendance(cls, check_in_dt, check_out_dt=None, context=None, **kwargs):
        vals = {
            "employee_id": cls.employee.id,
            "check_in": check_in_dt,
        }
        if check_out_dt:
            vals["check_out"] = check_out_dt
        vals.update(kwargs)
        env = (
            cls.env(context={**cls.env.context, **(context or {})})
            if context
            else cls.env
        )
        return env["hr.attendance"].create(vals)

    @classmethod
    def _create_fixed_attendance(cls, hours=8, check_in_hour=8, context=None, **kwargs):
        """Create attendance with fixed naive datetimes (same day, no midnight cross).

        Default: 2026-01-07 (Wednesday) 08:00-16:00.
        Employee must have tz="UTC" (set in setUpClass) for deterministic midnight.
        Odoo Datetime fields require naive datetimes (no tzinfo).
        """
        base = datetime(2026, 1, 7, check_in_hour, 0, 0)
        check_out = base.replace(hour=check_in_hour + hours)
        assert (
            check_out.date() == base.date()
        ), f"Crosses midnight: {base} -> {check_out}"
        return cls._create_attendance(base, check_out, context=context, **kwargs)

    @classmethod
    def _create_fixed_midnight_cross_attendance(
        cls, check_in_hour=22, hours=8, context=None, **kwargs
    ):
        """Create attendance crossing midnight in UTC (for segment_mode tests).

        Default: 2026-01-09 (Friday) 22:00 -> 2026-01-10 06:00.
        """
        base = datetime(2026, 1, 9, check_in_hour, 0, 0)
        next_hour = (check_in_hour + hours) % 24
        days = 1 if (check_in_hour + hours) >= 24 else 0
        check_out = (base + timedelta(days=days)).replace(hour=next_hour)
        return cls._create_attendance(base, check_out, context=context, **kwargs)

    @classmethod
    def _make_calendar(
        cls, days, tz=None, hour_from=8, hour_to=17, name="Test Calendar"
    ):
        """Create a resource.calendar with *days* daily slots hour_from→hour_to."""
        vals = {
            "name": name,
            "company_id": cls.company.id,
            "attendance_ids": [
                (
                    0,
                    0,
                    {
                        "name": f"Day {wd}",
                        "dayofweek": str(wd),
                        "hour_from": hour_from,
                        "hour_to": hour_to,
                    },
                )
                for wd in range(days)
            ],
        }
        if tz:
            vals["tz"] = tz
        return cls.env["resource.calendar"].create(vals)

    @classmethod
    def _make_rule(cls, name, credit_type=None, **overrides):
        """Create a time credit rule with defaults (domain condition, sequence 10)."""
        vals = {
            "name": name,
            "credit_type_id": (credit_type or cls.credit_type).id,
            "company_id": cls.company.id,
            "condition_type": "domain",
            "domain": "[]",
            "minutes_type": "fixed",
            "sequence": 10,
        }
        vals.update(overrides)
        return cls.env["hr.attendance.time.credit.rule"].create(vals)

    @classmethod
    def _make_credit_type(cls, name, code, **overrides):
        """Create a time credit type."""
        vals = {"name": name, "code": code, "company_id": cls.company.id}
        vals.update(overrides)
        return cls.env["hr.attendance.time.credit.type"].create(vals)

    @classmethod
    def _make_server_action(cls, name, code):
        """Create an ir.actions.server of type code on hr.attendance."""
        return cls.env["ir.actions.server"].create(
            {
                "name": name,
                "model_id": cls.hr_attendance_model_id,
                "state": "code",
                "code": code,
            }
        )
