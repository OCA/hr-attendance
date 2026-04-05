# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval

SERVER_ACTION_DOMAIN = (
    "[('model_id.model', '=', 'hr.attendance'), ('state', '=', 'code')]"
)

_logger = logging.getLogger(__name__)

# Fields whose changes require reprocessing all company attendances
_RULE_RECOMPUTE_TRIGGERS = {
    "active",
    "company_id",
    "allowance_type_id",
    "condition_type",
    "domain",
    "condition_action_id",
    "minutes_type",
    "minutes_fixed",
    "minutes_action_id",
    "rate",
    "minutes_cap",
    "sequence",
}


class HrAttendanceAllowanceRule(models.Model):
    _name = "hr.attendance.allowance.rule"
    _description = "Attendance Allowance Rule"
    _order = "sequence, id"

    name = fields.Char(
        required=True,
        translate=True,
        help="Descriptive name that identifies the purpose of this rule, "
        "e.g. 'Travel Time', 'Dressing Time', 'Paid Break'.",
    )
    sequence = fields.Integer(
        default=10,
        help="Evaluation order; rules with a lower sequence number are applied first.",
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this rule is skipped during allowance processing.",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        help="Restrict this rule to attendances belonging to employees "
        "of this company.",
    )
    allowance_type_id = fields.Many2one(
        "hr.attendance.allowance.type",
        required=True,
        help="Type of allowance that will be created when this rule's "
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
        [("fixed", "Fixed"), ("server_action", "Server Action")],
        required=True,
        default="fixed",
        help="Fixed: a constant number of minutes. "
        "Server Action: computes minutes dynamically via an ir.actions.server "
        "of type 'code'. The action must set `action = <integer>` with the "
        "number of minutes.",
    )
    minutes_fixed = fields.Integer(
        default=0,
        help="Fixed number of minutes granted when the rule condition is satisfied.",
    )
    minutes_action_id = fields.Many2one(
        "ir.actions.server",
        string="Minutes Server Action",
        domain=SERVER_ACTION_DOMAIN,
        help="Server action that computes the allowance minutes. "
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
        """Trigger allowance recompute for all eligible attendances of *companies*."""
        self = companies.env["hr.attendance"]
        attendances = self.search(
            [
                ("employee_id.company_id", "in", companies.ids),
                ("check_out", "!=", False),
                ("skip_allowance", "=", False),
                ("allowance_locked", "=", False),
            ]
        )
        if attendances:
            _logger.info(
                "Rule changed: reprocessing %d attendance(s) for companies %s.",
                len(attendances),
                companies.mapped("name"),
            )
            attendances._recompute_automatic_allowances()

    def unlink(self):
        companies = self.mapped("company_id")
        result = super().unlink()
        self._recompute_attendances_for_companies(companies)
        return result

    # -- Rule evaluation --

    def _run_server_action(self, action, attendance):
        """Run a server action in the context of a single attendance record."""
        ctx = {
            "active_model": "hr.attendance",
            "active_id": attendance.id,
            "active_ids": attendance.ids,
        }
        return action.with_context(**ctx).run()

    def _evaluate(self, attendance):
        self.ensure_one()
        if attendance.skip_allowance:
            return False
        # Evaluate condition
        try:
            if self.condition_type == "domain":
                dom = safe_eval(self.domain or "[]")
                if not attendance.filtered_domain(dom):
                    return False
            elif self.condition_type == "server_action":
                if not self.condition_action_id:
                    return False
                result = self._run_server_action(self.condition_action_id, attendance)
                if not result:
                    return False
        except Exception:
            _logger.warning(
                "Allowance rule '%s' condition failed on attendance %s",
                self.name,
                attendance.id,
                exc_info=True,
            )
            return False
        # Compute minutes
        try:
            if self.minutes_type == "fixed":
                minutes = self.minutes_fixed
            elif not self.minutes_action_id:
                return 0
            else:
                result = self._run_server_action(self.minutes_action_id, attendance)
                minutes = int(result) if result else 0
        except Exception:
            _logger.warning(
                "Allowance rule '%s' minutes computation failed on attendance %s",
                self.name,
                attendance.id,
                exc_info=True,
            )
            return False
        minutes = int(minutes * self.rate)
        if self.minutes_cap and minutes > self.minutes_cap:
            minutes = self.minutes_cap
        return minutes
