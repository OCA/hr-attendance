# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

_RECOMPUTE_TRIGGERS = {"check_in", "check_out", "skip_allowance"}


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    allowance_ids = fields.One2many(
        "hr.attendance.allowance",
        "attendance_id",
        help="Time allowances applied to this attendance record, either automatically "
        "by the rule engine or added manually by a manager.",
    )
    skip_allowance = fields.Boolean(
        default=False,
        groups="hr_attendance.group_hr_attendance_manager",
        help="When enabled, the allowance rule engine will ignore this attendance "
        "record entirely. Restricted to attendance managers to prevent employees "
        "from excluding themselves from allowance computation.",
    )
    allowance_locked = fields.Boolean(
        default=False,
        groups="hr_attendance.group_hr_attendance_manager",
        help="When enabled, allowance lines on this record are frozen: automatic "
        "recomputation, rule-change cascades, cron sweeps and manual force "
        "reprocess are all skipped. Unlock the record before making changes.",
    )
    total_credited_hours = fields.Float(
        compute="_compute_total_credited_hours",
        store=True,
        digits=(16, 2),
        help="Worked hours plus all credited allowance minutes converted to hours. "
        "Allowances represent supplementary credits (travel time, dressing time, "
        "paid breaks, etc.) that are distinct from worked time; this field combines "
        "both for reporting and payroll reference.",
    )

    @api.depends("allowance_ids.minutes", "worked_hours")
    def _compute_total_credited_hours(self):
        for record in self:
            allowance_hours = sum(record.allowance_ids.mapped("minutes")) / 60
            record.total_credited_hours = (record.worked_hours or 0.0) + allowance_hours

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("skip_allowance_recompute"):
            records.filtered("check_out")._recompute_automatic_allowances()
        return records

    def write(self, vals):
        result = super().write(vals)
        if _RECOMPUTE_TRIGGERS & set(vals) and not self.env.context.get(
            "skip_allowance_recompute"
        ):
            self._recompute_automatic_allowances()
        return result

    def _recompute_automatic_allowances(self):
        """Replace automatic allowance lines based on current rules.

        Locked records (``allowance_locked=True``) are silently skipped.
        Manual lines (``origin='manual'``) are never touched.  Records without
        ``check_out`` or with ``skip_allowance`` get their automatic lines
        removed and nothing else.
        """
        records = self.filtered(lambda r: not r.allowance_locked)
        if not records:
            return
        AllowanceModel = self.env["hr.attendance.allowance"]
        RuleModel = self.env["hr.attendance.allowance.rule"]
        company_ids = records.mapped("employee_id.company_id").ids
        if company_ids:
            rules_by_company = {}
            all_rules = RuleModel.search(
                [("company_id", "in", company_ids)], order="sequence, id"
            )
            for rule in all_rules:
                rules_by_company.setdefault(rule.company_id.id, RuleModel.browse())
                rules_by_company[rule.company_id.id] |= rule
        else:
            rules_by_company = {}
        for att in records:
            att.allowance_ids.filtered(lambda line: line.origin == "automatic").unlink()
            if not att.check_out or att.skip_allowance:
                continue
            company_rules = rules_by_company.get(
                att.employee_id.company_id.id, RuleModel.browse()
            )
            for rule in company_rules:
                result = rule._evaluate(att)
                if result and result > 0:
                    AllowanceModel.create(
                        {
                            "attendance_id": att.id,
                            "type_id": rule.allowance_type_id.id,
                            "minutes": result,
                            "origin": "automatic",
                        }
                    )

    def action_process_allowances(self):
        """Force reprocess — available as a server action on the list view."""
        self._recompute_automatic_allowances()
        _logger.info(
            "Force allowance reprocess: %d attendance(s).",
            len(self),
        )
        return True

    @api.model
    def _cron_process_allowances(self):
        """Safety-net sweep for attendances that may have been missed."""
        attendances = self.search(
            [
                ("check_out", "!=", False),
                ("skip_allowance", "=", False),
                ("allowance_locked", "=", False),
            ]
        )
        if not attendances:
            _logger.info("Cron allowance sweep: nothing to process.")
            return
        _logger.info(
            "Cron allowance sweep: reprocessing %d attendance(s).",
            len(attendances),
        )
        attendances._recompute_automatic_allowances()
