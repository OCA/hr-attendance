# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import logging

import odoo.tools.safe_eval as safe_eval_mod
from odoo import Command, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools.safe_eval import safe_eval

SERVER_ACTION_DOMAIN = (
    "[('model_id.model', '=', 'hr.attendance'), ('state', '=', 'code')]"
)

_logger = logging.getLogger(__name__)

SEGMENT_MODE_SELECTION = [
    ("consolidate", "Consolidated"),
    ("segment", "Segmented"),
]

# Fields whose changes require reprocessing all company attendances
_RULE_RECOMPUTE_TRIGGERS = {
    "active",
    "company_id",
    "credit_type_id",
    "condition_type",
    "domain",
    "condition_action_id",
    "minutes_type",
    "minutes_fixed",
    "minutes_action_id",
    "factor_value",
    "factor_base",
    "rate",
    "minutes_cap",
    "sequence",
    "calendar_id",
    "employee_id",
    "segment_mode",
}


class HrAttendanceTimeCreditRule(models.Model):
    _name = "hr.attendance.time.credit.rule"
    _description = "Attendance Time Credit Rule"
    _order = "sequence, id"

    name = fields.Char(
        required=True,
        translate=True,
        help="Descriptive name that identifies the purpose of this rule, "
        "e.g. 'Travel Time', 'Dressing Time', 'Sunday Premium'.",
    )
    sequence = fields.Integer(
        default=10,
        help="Evaluation order; rules with a lower sequence number are applied first.",
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this rule is skipped during time credit processing.",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        help="Restrict this rule to attendances belonging to employees "
        "of this company.",
    )
    calendar_id = fields.Many2one(
        "resource.calendar",
        help="Restrict this rule to employees using this specific work calendar. "
        "Takes priority over company-level rules for the same credit type.",
    )
    employee_id = fields.Many2one(
        "hr.employee",
        help="Restrict this rule to a specific employee. "
        "Takes priority over calendar- and company-level rules "
        "for the same credit type.",
    )
    credit_type_id = fields.Many2one(
        "hr.attendance.time.credit.type",
        required=True,
        help="Type of time credit that will be created when this rule's "
        "condition is met.",
    )
    condition_type = fields.Selection(
        [("domain", "Domain"), ("server_action", "Server Action")],
        required=True,
        default="domain",
        help="Domain: Odoo domain filter on the attendance record. "
        "Server Action: delegates condition evaluation to an ir.actions.server "
        "of type 'code'. The action must set `action = True` to trigger the rule.",
    )
    domain = fields.Char(
        default="[]",
        help="Odoo domain filter evaluated against the attendance record. "
        "The rule applies only when the attendance matches this domain.",
    )
    condition_action_id = fields.Many2one(
        "ir.actions.server",
        string="Condition Server Action",
        domain=SERVER_ACTION_DOMAIN,
        help="Server action evaluated to determine if the rule applies. "
        "The action code must set `action = True` for the rule to trigger. "
        "Available context: record (the attendance), env, model, datetime, "
        "dateutil, time, timezone.",
    )
    minutes_type = fields.Selection(
        [
            ("fixed", "Fixed"),
            ("server_action", "Server Action"),
            ("worked_time_factor", "Worked Time Factor"),
        ],
        required=True,
        default="fixed",
        help="Fixed: a constant number of minutes. "
        "Server Action: computes minutes dynamically via an ir.actions.server "
        "of type 'code'. The action must set `action = <integer>` with the "
        "number of minutes. "
        "Worked Time Factor: credits additional time as a multiple of worked hours "
        "(or accumulated credited hours). E.g. factor 1.5 on 8h → 4h extra credit.",
    )
    minutes_fixed = fields.Integer(
        default=0,
        help="Fixed number of minutes granted when the rule condition is satisfied.",
    )
    minutes_action_id = fields.Many2one(
        "ir.actions.server",
        string="Minutes Server Action",
        domain=SERVER_ACTION_DOMAIN,
        help="Server action that computes the credit minutes. "
        "The action code must set `action = <integer>` with the minutes value. "
        "Available context: record (the attendance), env, model, datetime, "
        "dateutil, time, timezone.",
    )
    rate = fields.Float(
        default=1.0,
        help="Multiplier applied to the computed minutes before rounding. "
        "Use 0.5 to grant half the computed time, 1.5 for time and a half, etc.",
    )
    minutes_cap = fields.Integer(
        default=0,
        help="Maximum minutes this rule can grant per attendance (0 = no cap). "
        "Applied after the rate multiplier.",
    )
    factor_value = fields.Float(
        default=1.5,
        help="Multiplier applied to worked time when minutes_type is "
        "'worked_time_factor'. The credit equals the additional time beyond the base: "
        "minutes = base_hours * 60 * (factor - 1.0). "
        "E.g. factor 1.5 on 8 hours → 4 hours credit → total 12 hours.",
    )
    factor_base = fields.Selection(
        [
            ("worked_hours", "Worked Hours Only"),
            ("credited_hours", "Worked Hours + Prior Credits"),
        ],
        default="worked_hours",
        help="What the factor is applied to when minutes_type is "
        "'worked_time_factor'. "
        "'Worked Hours + Prior Credits' uses the accumulated total from rules "
        "evaluated earlier (lower sequence number).",
    )
    segment_mode = fields.Selection(
        [("", "Inherit from credit type")] + SEGMENT_MODE_SELECTION,
        default="",
        help="Empty = inherit from credit type. 'Consolidated' produces one credit "
        "line per attendance even when it crosses midnight. 'Segmented' evaluates "
        "each calendar-day segment independently (current default behavior).",
    )

    def _get_effective_segment_mode(self):
        """Return the resolved segment mode for this rule.

        Checks the rule-level override first; falls back to the credit type's
        default; ultimate fallback is 'consolidate'.
        """
        self.ensure_one()
        return self.segment_mode or self.credit_type_id.segment_mode or "consolidate"

    # -- Rule-change cascade --

    def write(self, vals):
        if _RULE_RECOMPUTE_TRIGGERS & set(vals):
            companies_before = self.mapped("company_id")
        result = super().write(vals)
        if _RULE_RECOMPUTE_TRIGGERS & set(vals):
            companies_after = self.mapped("company_id")
            affected_companies = companies_before | companies_after
            self._recompute_attendances_for_companies(affected_companies)
        return result

    @classmethod
    def _recompute_attendances_for_companies(cls, companies):
        """Trigger time credit recompute for all eligible attendances of *companies*."""
        self = companies.env["hr.attendance"]
        attendances = self.search(
            [
                ("employee_id.company_id", "in", companies.ids),
                ("check_out", "!=", False),
                ("skip_time_credit", "=", False),
                ("credit_locked", "=", False),
            ]
        )
        if attendances:
            _logger.info(
                "Rule changed: reprocessing %d attendance(s) for companies %s.",
                len(attendances),
                companies.mapped("name"),
            )
            attendances._recompute_automatic_time_credits()

    def unlink(self):
        companies = self.mapped("company_id")
        result = super().unlink()
        self._recompute_attendances_for_companies(companies)
        return result

    # -- Rule evaluation --

    def _run_server_action(self, action, attendance, **segment_context):
        """Run a server action in the context of a single attendance record.

        When ``segment_context`` is empty (non-segmented path), the standard
        ``action.run()`` path is used for full compatibility with all server
        action types (``code``, ``object_create``, ``email``, etc.).

        When ``segment_context`` is provided (segmented path), the server
        action code is evaluated directly via ``safe_eval`` with per-segment
        context variables injected as top-level namespace keys:
        ``segment_date``, ``segment_hours``, ``segment_day_type``,
        ``segment_is_holiday``.
        """
        if not action or not action.code:
            return False
        if not segment_context:
            ctx = {
                "active_model": "hr.attendance",
                "active_id": attendance.id,
                "active_ids": attendance.ids,
            }
            return action.with_context(**ctx).run()

        def _noop_log(message, level="info"):
            _logger.log(getattr(logging, level.upper(), logging.INFO), message)

        eval_context = {
            "uid": self.env.uid,
            "user": self.env.user,
            "time": safe_eval_mod.time,
            "datetime": safe_eval_mod.datetime,
            "dateutil": safe_eval_mod.dateutil,
            "timezone": safe_eval_mod.pytz.timezone,
            "float_compare": float_compare,
            "b64encode": base64.b64encode,
            "b64decode": base64.b64decode,
            "Command": Command,
            "env": self.env,
            "model": self.env["hr.attendance"],
            "UserError": UserError,
            "record": attendance,
            "records": attendance,
            "log": _noop_log,
        }
        eval_context.update(segment_context)
        safe_eval(
            action.code.strip(),
            eval_context,
            mode="exec",
            nocopy=True,
            filename=str(action),
        )
        return eval_context.get("action")

    def _matches_condition(self, attendance, **segment_context):
        """Return True if the rule's condition is satisfied for *attendance*.

        Domain conditions are evaluated against the attendance record; server
        action conditions receive ``segment_context`` (if any) in their eval
        context. Returns False (and logs) on any evaluation error.
        """
        self.ensure_one()
        try:
            if self.condition_type == "domain":
                dom = safe_eval(self.domain or "[]")
                return bool(attendance.filtered_domain(dom))
            if not self.condition_action_id:
                return False
            return bool(
                self._run_server_action(
                    self.condition_action_id, attendance, **segment_context
                )
            )
        except Exception:
            _logger.warning(
                "Time credit rule '%s' condition failed on attendance %s",
                self.name,
                attendance.id,
                exc_info=True,
            )
            return False

    def _compute_minutes(
        self,
        attendance,
        base_hours=None,
        accumulated_hours=None,
        apply_rate=False,
        **segment_context,
    ):
        """Return the raw minutes a rule grants, or False on error.

        ``base_hours`` overrides the worked-hours base (segmented path passes
        per-day hours). ``apply_rate`` preserves the segmented path's single
        truncation factor formula. A missing minutes server action returns 0.
        """
        self.ensure_one()
        try:
            if self.minutes_type == "fixed":
                minutes = self.minutes_fixed
            elif self.minutes_type == "worked_time_factor":
                if (
                    self.factor_base == "credited_hours"
                    and accumulated_hours is not None
                ):
                    base_hours = accumulated_hours
                elif base_hours is None:
                    base_hours = attendance.worked_hours or 0.0
                raw = base_hours * 60 * (self.factor_value - 1.0)
                minutes = int(raw) if not apply_rate else int(raw * self.rate)
            elif not self.minutes_action_id:
                return 0
            else:
                result = self._run_server_action(
                    self.minutes_action_id, attendance, **segment_context
                )
                minutes = int(result) if result else 0
            return minutes
        except Exception:
            _logger.warning(
                "Time credit rule '%s' minutes computation failed on attendance %s",
                self.name,
                attendance.id,
                exc_info=True,
            )
            return False

    def _finalize_minutes(self, minutes):
        """Apply the rate multiplier and the per-computation minutes cap."""
        self.ensure_one()
        minutes = int(minutes * self.rate)
        if self.minutes_cap and minutes > self.minutes_cap:
            minutes = self.minutes_cap
        return minutes

    def _evaluate(self, attendance, accumulated_hours=None):
        """Evaluate the rule against an attendance record.

        :param attendance: hr.attendance record to evaluate.
        :param accumulated_hours: Optional float. When factor_base is
            'credited_hours', this value (worked_hours + prior credits) is used
            as the base for the factor calculation instead of worked_hours alone.
            Provided by the recompute loop for rules evaluated in sequence.
        :return: Integer minutes to credit, 0 if none, or False on error/skip.
        """
        self.ensure_one()
        if attendance.skip_time_credit:
            return False
        if not self._matches_condition(attendance):
            return False
        minutes = self._compute_minutes(attendance, accumulated_hours=accumulated_hours)
        if minutes is False:
            return False
        return self._finalize_minutes(minutes)
