# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
from datetime import datetime, time, timedelta

from pytz import timezone, utc

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

from odoo.addons.resource.models.utils import Intervals

_logger = logging.getLogger(__name__)

_RECOMPUTE_TRIGGERS = {
    "check_in",
    "check_out",
    "skip_time_credit",
    "employee_id",
    "is_public_holiday",
}


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    time_credit_ids = fields.One2many(
        "hr.attendance.time.credit",
        "attendance_id",
        help="Time credits applied to this attendance record, either automatically "
        "by the rule engine or added manually by a manager.",
    )
    skip_time_credit = fields.Boolean(
        default=False,
        groups="hr_attendance.group_hr_attendance_manager",
        help="When enabled, the time credit rule engine will ignore this attendance "
        "record entirely. Restricted to attendance managers to prevent employees "
        "from excluding themselves from credit computation.",
    )
    credit_locked = fields.Boolean(
        default=False,
        groups="hr_attendance.group_hr_attendance_manager",
        help="When enabled, credit lines on this record are frozen: automatic "
        "recomputation, rule-change cascades, cron sweeps and manual force "
        "reprocess are all skipped. Unlock the record before making changes.",
    )
    check_in_day_type = fields.Selection(
        [("working_day", "Working Day"), ("non_working_day", "Non-Working Day")],
        compute="_compute_check_in_day_type",
        store=True,
        help="Day type based on the employee's working schedule. "
        "A day with no scheduled attendance in the resource calendar "
        "is classified as non-working (weekend or rest day).",
    )
    total_credited_hours = fields.Float(
        compute="_compute_total_credited_hours",
        store=True,
        digits=(16, 2),
        help="Worked hours plus all credited minutes converted to hours. "
        "Time credits represent supplementary credits (travel time, dressing time, "
        "paid breaks, weekend premiums, etc.) that are distinct from worked time; "
        "this field combines both for reporting and payroll reference.",
    )
    is_public_holiday = fields.Boolean(
        compute="_compute_is_public_holiday",
        store=True,
        help="True when the check-in date (in the employee's local timezone) "
        "is covered by a global calendar leave on the employee's work schedule. "
        "Employee-specific leave days are not considered public holidays.",
    )

    @api.depends("check_in", "employee_id", "employee_id.resource_calendar_id")
    def _compute_check_in_day_type(self):
        for record in self:
            if not record.check_in or not record.employee_id:
                record.check_in_day_type = False
                continue
            calendar = record._get_employee_calendar()
            if not calendar:
                record.check_in_day_type = "working_day"
                continue
            tz_name = record.employee_id._get_tz()
            local_dt = utc.localize(record.check_in).astimezone(timezone(tz_name))
            weekday = str(local_dt.weekday())
            has_attendance = calendar.attendance_ids.filtered(
                lambda a, wd=weekday: a.dayofweek == wd and not a.display_type
            )
            record.check_in_day_type = (
                "working_day" if has_attendance else "non_working_day"
            )

    @api.depends("time_credit_ids.minutes", "worked_hours")
    def _compute_total_credited_hours(self):
        for record in self:
            credit_hours = sum(record.time_credit_ids.mapped("minutes")) / 60
            record.total_credited_hours = (record.worked_hours or 0.0) + credit_hours

    @api.depends("check_in", "employee_id", "employee_id.resource_calendar_id")
    def _compute_is_public_holiday(self):
        for record in self:
            if not record.check_in or not record.employee_id:
                record.is_public_holiday = False
                continue
            calendar = record._get_employee_calendar()
            if not calendar:
                record.is_public_holiday = False
                continue
            tz_name = record.employee_id._get_tz()
            local_date = (
                utc.localize(record.check_in).astimezone(timezone(tz_name)).date()
            )
            record.is_public_holiday = record._has_global_leave_on(calendar, local_date)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("skip_time_credit_recompute"):
            records.filtered("check_out")._recompute_automatic_time_credits()
        return records

    def write(self, vals):
        result = super().write(vals)
        if _RECOMPUTE_TRIGGERS & set(vals) and not self.env.context.get(
            "skip_time_credit_recompute"
        ):
            self._recompute_automatic_time_credits()
        return result

    def _recompute_automatic_time_credits(self):
        """Replace automatic credit lines based on current rules.

        Locked records (``credit_locked=True``) are silently skipped.
        Manual lines (``origin='manual'``) are never touched.  Records without
        ``check_out`` or with ``skip_time_credit`` get their automatic lines
        removed and nothing else.
        """
        records = self.filtered(lambda r: not r.credit_locked)
        if not records:
            return
        CreditModel = self.env["hr.attendance.time.credit"]
        RuleModel = self.env["hr.attendance.time.credit.rule"]
        company_ids = records.mapped("employee_id.company_id").ids
        rules_by_company = {}
        if company_ids:
            all_rules = RuleModel.search(
                [("company_id", "in", company_ids)], order="sequence, id"
            )
            for rule in all_rules:
                rules_by_company.setdefault(rule.company_id.id, RuleModel.browse())
                rules_by_company[rule.company_id.id] |= rule
        for att in records:
            att.time_credit_ids.filtered(
                lambda line: line.origin == "automatic"
            ).unlink()
            if not att.check_out or att.skip_time_credit:
                continue
            company_rules = rules_by_company.get(
                att.employee_id.company_id.id, RuleModel.browse()
            )
            accumulated_minutes = att._apply_rules(company_rules, CreditModel)
            _logger.debug(
                "Attendance %s: %d minute(s) credited.", att.id, accumulated_minutes
            )

    def _apply_rules(self, rules, CreditModel):
        """Apply *rules* to this attendance; return total accumulated minutes."""
        self.ensure_one()
        if not self.check_out or self.skip_time_credit:
            return 0
        employee = self.employee_id
        calendar = (
            employee.resource_calendar_id or employee.company_id.resource_calendar_id
        )
        rules_by_type = {}
        for rule in rules:
            rules_by_type.setdefault(rule.credit_type_id, []).append(rule)
        filtered_rules = []
        for _credit_type, type_rules in rules_by_type.items():
            # Scope hierarchy: employee > calendar > company
            employee_rules = [r for r in type_rules if r.employee_id == employee]
            if employee_rules:
                filtered_rules.extend(employee_rules)
                continue
            calendar_rules = [
                r for r in type_rules if r.calendar_id == calendar and not r.employee_id
            ]
            if calendar_rules:
                filtered_rules.extend(calendar_rules)
                continue
            company_rules = [
                r for r in type_rules if not r.calendar_id and not r.employee_id
            ]
            filtered_rules.extend(company_rules)
        accumulated_minutes = 0
        for rule in filtered_rules:
            accumulated_hours = (self.worked_hours or 0.0) + accumulated_minutes / 60.0
            effective_mode = rule._get_effective_segment_mode()
            segments = (
                self._get_day_segments() if self.check_in and self.check_out else []
            )
            if segments and (len(segments) > 1 or effective_mode == "segment"):
                if effective_mode == "consolidate":
                    accumulated_minutes += self._apply_rule_consolidated(
                        rule, CreditModel, accumulated_hours
                    )
                else:
                    accumulated_minutes += self._apply_rule_segmented(
                        rule, CreditModel, accumulated_hours
                    )
            else:
                result = rule._evaluate(self, accumulated_hours=accumulated_hours)
                if result and result > 0:
                    CreditModel.create(
                        {
                            "attendance_id": self.id,
                            "type_id": rule.credit_type_id.id,
                            "minutes": result,
                            "origin": "automatic",
                            "rule_id": rule.id,
                        }
                    )
                    accumulated_minutes += result
        return accumulated_minutes

    def _apply_rule_segmented(self, rule, CreditModel, accumulated_hours=None):
        """Apply a factor rule segment-by-segment across calendar days.

        For attendances that span midnight, each calendar-day portion is
        evaluated independently so that different day-type factors can apply
        to different portions.

        :return: Total minutes credited across all segments.

        If a segment's minutes computation errors, the rule is skipped for
        this attendance and ``False`` is returned; credit lines already
        created for earlier segments remain committed.
        """
        self.ensure_one()
        total_minutes = 0
        remaining_cap = rule.minutes_cap
        for seg_date, seg_hours in self._get_day_segments():
            seg_day_type, seg_is_holiday = self._get_day_type_for_date(seg_date)
            if not self._segment_matches_condition(
                rule, seg_day_type, seg_is_holiday, seg_date, seg_hours
            ):
                continue
            minutes = rule._compute_minutes(
                self,
                base_hours=seg_hours,
                accumulated_hours=accumulated_hours,
                apply_rate=True,
                segment_date=seg_date,
                segment_hours=seg_hours,
                segment_day_type=seg_day_type,
                segment_is_holiday=seg_is_holiday,
            )
            if minutes is False:
                return False
            if rule.minutes_cap:
                minutes = min(minutes, remaining_cap)
                remaining_cap -= minutes
            if minutes > 0:
                CreditModel.create(
                    {
                        "attendance_id": self.id,
                        "type_id": rule.credit_type_id.id,
                        "minutes": minutes,
                        "origin": "automatic",
                        "segment_date": seg_date,
                        "segment_hours": seg_hours,
                        "rule_id": rule.id,
                    }
                )
                total_minutes += minutes
        return total_minutes

    def _apply_rule_consolidated(self, rule, CreditModel, accumulated_hours=None):
        """Apply a rule to the whole attendance without per-segment splitting.

        Condition is evaluated once. Minutes are computed from total worked_hours
        (or accumulated_hours for credited_hours factor_base). A single credit
        line is created.

        :return: Minutes credited (0 if condition failed or minutes zero).
        """
        self.ensure_one()
        result = rule._evaluate(self, accumulated_hours=accumulated_hours)
        if result and result > 0:
            CreditModel.create(
                {
                    "attendance_id": self.id,
                    "type_id": rule.credit_type_id.id,
                    "minutes": result,
                    "origin": "automatic",
                    "rule_id": rule.id,
                }
            )
        return result or 0

    def _segment_matches_condition(
        self, rule, seg_day_type, seg_is_holiday=False, seg_date=None, seg_hours=None
    ):
        """Return True if the rule's condition is satisfied for this segment.

        For domain conditions, ``check_in_day_type`` criteria are matched
        against *seg_day_type* instead of the stored field value so that
        midnight-crossing attendances evaluate correctly per segment.
        """
        self.ensure_one()
        if rule.condition_type == "domain":
            return self._domain_matches_segment(
                rule.domain or "[]", seg_day_type, seg_is_holiday
            )
        return rule._matches_condition(
            self,
            segment_date=seg_date,
            segment_hours=seg_hours,
            segment_day_type=seg_day_type,
            segment_is_holiday=seg_is_holiday,
        )

    def _domain_matches_segment(self, domain_str, seg_day_type, seg_is_holiday=False):
        """Evaluate *domain_str* substituting ``check_in_day_type`` for *seg_day_type*.

        Any ``check_in_day_type`` leaf in the domain is resolved against the
        segment's day type instead of the stored field.  All other criteria
        are evaluated normally via ``filtered_domain``.
        """
        try:
            dom = safe_eval(domain_str)
        except Exception:
            _logger.warning(
                "Time credit: malformed domain '%s' on attendance %s",
                domain_str,
                self.id,
                exc_info=True,
            )
            return False
        adjusted = []
        for criterion in dom:
            if (
                isinstance(criterion, list | tuple)
                and criterion[0] == "check_in_day_type"
            ):
                op, val = criterion[1], criterion[2]
                if op == "=":
                    if seg_day_type != val:
                        return False
                elif op == "!=":
                    if seg_day_type == val:
                        return False
                else:
                    adjusted.append(criterion)
            elif (
                isinstance(criterion, list | tuple)
                and criterion[0] == "is_public_holiday"
            ):
                op, val = criterion[1], criterion[2]
                if op == "=":
                    if seg_is_holiday != val:
                        return False
                elif op == "!=":
                    if seg_is_holiday == val:
                        return False
                else:
                    adjusted.append(criterion)
            else:
                adjusted.append(criterion)
        return bool(self.filtered_domain(adjusted)) if adjusted else True

    def action_process_time_credits(self):
        """Force reprocess — available as a server action on the list view."""
        self._recompute_automatic_time_credits()
        _logger.info(
            "Force time credit reprocess: %d attendance(s).",
            len(self),
        )
        return True

    @api.model
    def _cron_process_time_credits(self):
        """Safety-net sweep for attendances that may have been missed."""
        lookback = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_attendance_time_credit.cron_lookback_days", default=90)
        )
        domain = [
            ("check_out", "!=", False),
            ("skip_time_credit", "=", False),
            ("credit_locked", "=", False),
        ]
        if lookback:
            cutoff = fields.Datetime.now() - timedelta(days=lookback)
            domain.append(("check_in", ">=", cutoff))
        attendances = self.search(domain)
        if not attendances:
            _logger.info("Cron time credit sweep: nothing to process.")
            return
        _logger.info(
            "Cron time credit sweep: reprocessing %d attendance(s).",
            len(attendances),
        )
        attendances._recompute_automatic_time_credits()

    # -- Day-segmentation helpers --

    def _get_employee_calendar(self):
        """Resolve the calendar for this attendance's employee (or company fallback)."""
        self.ensure_one()
        return (
            self.employee_id.resource_calendar_id
            or self.employee_id.company_id.resource_calendar_id
        )

    def _has_global_leave_on(self, calendar, target_date):
        """Return True if a global calendar leave covers *target_date* (local).

        ``calendar.leaves`` stores ``date_from``/``date_to`` as naive UTC
        datetimes; the local-day boundaries are converted to UTC before
        searching.
        """
        self.ensure_one()
        tz_name = self.employee_id._get_tz()
        local_tz = timezone(tz_name)
        utc_start = (
            local_tz.localize(datetime.combine(target_date, time.min))
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        utc_end = (
            local_tz.localize(datetime.combine(target_date, time.max))
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        return bool(
            self.env["resource.calendar.leaves"].search(
                [
                    ("calendar_id", "=", calendar.id),
                    ("resource_id", "=", False),
                    ("date_from", "<=", fields.Datetime.to_string(utc_end)),
                    ("date_to", ">=", fields.Datetime.to_string(utc_start)),
                ],
                limit=1,
            )
        )

    def _compute_night_overlap_minutes(self, segment_date, factor=0.5):
        """Minutes of this attendance inside the night window (22:00-06:00 local)
        on *segment_date*, multiplied by *factor* (default 0.5 → 1.5x credit).

        The window is matched forward (22:00 → 06:00 next day) and backward
        (previous day 22:00 → 06:00) so segments starting after midnight are
        covered. Local times use the employee timezone. Overlap is computed
        with Odoo's ``Intervals`` intersection (as in hr_attendance core).
        """
        self.ensure_one()
        if not self.check_in or not self.check_out or not segment_date:
            return 0
        tz = timezone(self.employee_id._get_tz())
        check_in_local = utc.localize(self.check_in).astimezone(tz)
        check_out_local = utc.localize(self.check_out).astimezone(tz)
        prev_date = segment_date - timedelta(days=1)
        next_date = segment_date + timedelta(days=1)
        if segment_date == check_in_local.date():
            seg_start_local = check_in_local
        else:
            seg_start_local = tz.localize(datetime.combine(segment_date, time.min))
        if segment_date == check_out_local.date():
            seg_end_local = check_out_local
        else:
            seg_end_local = tz.localize(datetime.combine(next_date, time.min))
        night_window = Intervals(
            [
                (
                    tz.localize(datetime.combine(segment_date, time(22))),
                    tz.localize(datetime.combine(next_date, time(6))),
                    self,
                ),
                (
                    tz.localize(datetime.combine(prev_date, time(22))),
                    tz.localize(datetime.combine(segment_date, time(6))),
                    self,
                ),
            ]
        )
        segment = Intervals([(seg_start_local, seg_end_local, self)])
        overlap_minutes = sum(
            (stop - start).total_seconds() / 60.0
            for start, stop, _meta in segment & night_window
        )
        return int(overlap_minutes * factor)

    def _get_day_segments(self):
        """Split the attendance into per-calendar-day (date, hours) tuples.

        Returns a list of ``(date, float_hours)`` pairs, one per calendar day
        covered by the attendance.  Single-day attendances return a single
        element.  Attendances without ``check_out`` return an empty list.

        Uses the employee's timezone to determine calendar day boundaries.
        Falls back to UTC if no timezone is configured.
        """
        self.ensure_one()
        if not self.check_in or not self.check_out:
            return []
        tz_name = self.employee_id._get_tz()
        tz = timezone(tz_name)
        check_in_local = utc.localize(self.check_in).astimezone(tz)
        check_out_local = utc.localize(self.check_out).astimezone(tz)
        segments = []
        current_local = check_in_local
        current_utc = self.check_in
        while current_local.date() < check_out_local.date():
            local_midnight = (current_local + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            utc_midnight = local_midnight.astimezone(utc).replace(tzinfo=None)
            segment_hours = (utc_midnight - current_utc).total_seconds() / 3600
            if segment_hours > 0:
                segments.append((current_local.date(), segment_hours))
            current_local = local_midnight
            current_utc = utc_midnight
        # Final (or only) segment on check_out date
        segment_hours = (self.check_out - current_utc).total_seconds() / 3600
        if segment_hours > 0:
            segments.append((current_local.date(), segment_hours))
        return segments

    def _get_day_type_for_date(self, target_date):
        """Determine day type and holiday status for *target_date*.

        :param target_date: ``date`` object.
        :return: ``(day_type, is_holiday)`` tuple.
            day_type is ``'working_day'`` or ``'non_working_day'``.
            is_holiday is ``True`` if a global calendar leave covers the date.
        """
        self.ensure_one()
        calendar = self._get_employee_calendar()
        if not calendar:
            return ("working_day", False)
        weekday = str(target_date.weekday())
        has_attendance = calendar.attendance_ids.filtered(
            lambda a, wd=weekday: a.dayofweek == wd and not a.display_type
        )
        day_type = "working_day" if has_attendance else "non_working_day"
        return (day_type, self._has_global_leave_on(calendar, target_date))
