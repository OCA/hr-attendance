# Copyright 2023 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, time

import pytz

from odoo import api, fields, models
from odoo.tools import format_date


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    @api.model
    def get_allocation_data_request(self, target_date=None):
        """Always include the extra hours leave type in the allocation data."""
        extra_hours_time_off_type = self.env.ref(
            "hr_holidays_attendance.holiday_status_extra_hours",
            raise_if_not_found=False,
        )

        allocation_data = super().get_allocation_data_request(target_date)

        extra_hours_in_data = any(
            leave_type[3] == extra_hours_time_off_type.id
            for leave_type in allocation_data
        )

        if extra_hours_time_off_type and not extra_hours_in_data:
            employee = extra_hours_time_off_type.env[
                "hr.employee"
            ]._get_contextual_employee()
            extra_hours_data = extra_hours_time_off_type._prepare_extra_hours_data(
                employee, target_date
            )
            allocation_data.append(extra_hours_data)
        return allocation_data

    def _prepare_lt_info_detail(self):
        return {
            "remaining_leaves": 0,
            "virtual_remaining_leaves": 0,
            "max_leaves": 0,
            "accrual_bonus": 0,
            "leaves_taken": 0,
            "virtual_leaves_taken": 0,
            "leaves_requested": 0,
            "leaves_approved": 0,
            "closest_allocation_remaining": 0,
            "closest_allocation_expire": False,
            "holds_changes": False,
            "total_virtual_excess": 0,
            "virtual_excess_data": {},
            "exceeding_duration": 0,
            "request_unit": self.request_unit,
            "icon": self.sudo().icon_id.url,
            "allows_negative": self.allows_negative,
            "max_allowed_negative": self.max_allowed_negative,
        }

    def _prepare_extra_hours_data(self, employee, target_date):
        if target_date and isinstance(target_date, str):
            target_date = datetime.fromisoformat(target_date).date()
        elif target_date and isinstance(target_date, datetime):
            target_date = target_date.date()
        elif not target_date:
            target_date = fields.Date.today()
        allocations_leaves_consumed, extra_data = employee.with_context(
            ignored_leave_ids=self.env.context.get("ignored_leave_ids")
        )._get_consumed_leaves(self, target_date)
        lt_info = self._prepare_lt_info_detail()
        lt_info["exceeding_duration"] = extra_data[employee][self]["exceeding_duration"]
        for excess_date, excess_days in extra_data[employee][self][
            "excess_days"
        ].items():
            amount = excess_days["amount"]
            lt_info["virtual_excess_data"][
                excess_date.strftime("%Y-%m-%d")
            ] = excess_days
            lt_info["total_virtual_excess"] += amount
            if not self.allows_negative:
                continue
            lt_info["virtual_leaves_taken"] += amount
            lt_info["virtual_remaining_leaves"] -= amount
            if excess_days["is_virtual"]:
                lt_info["leaves_requested"] += amount
            else:
                lt_info["leaves_approved"] += amount
                lt_info["leaves_taken"] += amount
                lt_info["remaining_leaves"] -= amount
        allocations_now = self.env["hr.leave.allocation"]
        allocations_date = self.env["hr.leave.allocation"]
        allocations_with_remaining_leaves = self.env["hr.leave.allocation"]
        for allocation, data in allocations_leaves_consumed[employee][self].items():
            if allocation:
                today = fields.Date.today()
                if allocation.date_from <= today and (
                    not allocation.date_to or allocation.date_to >= today
                ):
                    allocations_now |= allocation
                if allocation.date_from <= target_date and (
                    not allocation.date_to or allocation.date_to >= target_date
                ):
                    allocations_date |= allocation
                if allocation.date_from > target_date:
                    continue
                if allocation.date_to and allocation.date_to < target_date:
                    continue
            lt_info["remaining_leaves"] += data["remaining_leaves"]
            lt_info["virtual_remaining_leaves"] += data["virtual_remaining_leaves"]
            lt_info["max_leaves"] += data["max_leaves"]
            lt_info["accrual_bonus"] += data["accrual_bonus"]
            lt_info["leaves_taken"] += data["leaves_taken"]
            lt_info["virtual_leaves_taken"] += data["virtual_leaves_taken"]
            lt_info["leaves_requested"] += (
                data["virtual_leaves_taken"] - data["leaves_taken"]
            )
            lt_info["leaves_approved"] += data["leaves_taken"]
            if data["virtual_remaining_leaves"] > 0:
                allocations_with_remaining_leaves |= allocation
        closest_allocation = (
            allocations_with_remaining_leaves[0]
            if allocations_with_remaining_leaves
            else self.env["hr.leave.allocation"]
        )
        closest_allocations = allocations_with_remaining_leaves.filtered(
            lambda ca: ca.date_to == closest_allocation.date_to
        )
        closest_allocation_remaining = sum(
            allocations_leaves_consumed[employee][self][ca]["virtual_remaining_leaves"]
            for ca in closest_allocations
        )
        if closest_allocation.date_to:
            closest_allocation_expire = format_date(
                self.env, closest_allocation.date_to
            )
            calendar = (
                employee.resource_calendar_id
                or employee.company_id.resource_calendar_id
            )
            closest_allocation_duration = (
                calendar._attendance_intervals_batch(
                    datetime.combine(closest_allocation.date_to, time.min).replace(
                        tzinfo=pytz.UTC
                    ),
                    datetime.combine(target_date, time.max).replace(tzinfo=pytz.UTC),
                )
                if self.request_unit == "hour"
                else (closest_allocation.date_to - target_date).days + 1
            )
        else:
            closest_allocation_expire = False
            closest_allocation_duration = False
        holds_changes = (
            lt_info["accrual_bonus"] > 0
            or bool(allocations_date - allocations_now)
            or bool(allocations_now - allocations_date)
        ) and target_date != fields.Date.today()

        lt_info.update(
            {
                "closest_allocation_remaining": closest_allocation_remaining,
                "closest_allocation_expire": closest_allocation_expire,
                "closest_allocation_duration": closest_allocation_duration,
                "holds_changes": holds_changes,
            }
        )
        return self.name, lt_info, self.requires_allocation, self.id
