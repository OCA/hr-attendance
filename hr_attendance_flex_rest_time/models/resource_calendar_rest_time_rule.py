# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendarRestTimeRule(models.Model):
    _name = "resource.calendar.rest.time.rule"
    _description = "Rest Time Rule"
    _order = "min_hours desc"
    _sql_constraints = [
        (
            "unique_calendar_min_hours",
            "unique(calendar_id, min_hours)",
            "A rule with the same minimum hours already exists for this calendar.",
        ),
    ]

    calendar_id = fields.Many2one(
        "resource.calendar", required=True, ondelete="cascade"
    )
    min_hours = fields.Float(
        required=True,
        help="Apply this rule when gross worked hours (check-out minus check-in) "
        "are greater than or equal to this value.",
    )
    rest_time = fields.Float(
        required=True,
        help="Rest time in hours to deduct when this rule applies.",
    )

    @api.constrains("min_hours")
    def _check_min_hours_positive(self):
        for rule in self:
            if rule.min_hours < 0:
                raise ValidationError(_("Minimum hours cannot be negative."))

    @api.constrains("rest_time")
    def _check_rest_time_positive(self):
        for rule in self:
            if rule.rest_time < 0:
                raise ValidationError(_("Rest time cannot be negative."))
