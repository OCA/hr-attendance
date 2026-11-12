# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    rest_time_rule_ids = fields.One2many(
        "resource.calendar.rest.time.rule",
        "calendar_id",
        string="Rest Time Rules",
    )

    def _get_rest_time(self, gross_hours):
        """Return rest time in hours based on gross worked hours and configured rules.

        Rules are evaluated from highest min_hours to lowest; the first matching rule
        (gross_hours >= rule.min_hours) is applied. Returns 0.0 if no rules are
        configured or none match.
        """
        self.ensure_one()
        for rule in self.rest_time_rule_ids.sorted("min_hours", reverse=True):
            if gross_hours >= rule.min_hours:
                return rule.rest_time
        return 0.0
