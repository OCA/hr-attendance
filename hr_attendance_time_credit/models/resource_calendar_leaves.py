# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    # Only these fields change whether a date is covered by a global leave.
    _PUBLIC_HOLIDAY_FIELDS = {"calendar_id", "resource_id", "date_from", "date_to"}

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        leaves._refresh_public_holiday_attendances()
        return leaves

    def write(self, vals):
        relevant = self._PUBLIC_HOLIDAY_FIELDS & set(vals)
        before = self._public_holiday_ranges() if relevant else []
        result = super().write(vals)
        if relevant:
            self._refresh_public_holiday_attendances(
                before + self._public_holiday_ranges()
            )
        return result

    def unlink(self):
        ranges = self._public_holiday_ranges()
        result = super().unlink()
        self._refresh_public_holiday_attendances(ranges)
        return result

    def _public_holiday_ranges(self):
        """Return the date ranges covered by the global leaves in this set."""
        return [
            (leave.date_from.date(), leave.date_to.date())
            for leave in self
            if not leave.resource_id and leave.date_from and leave.date_to
        ]

    def _refresh_public_holiday_attendances(self, ranges=None):
        """Keep ``is_public_holiday`` and its credits in sync with the leaves.

        A global leave is a public holiday for every employee on the calendar,
        so the attendances of the affected dates have to be re-evaluated.
        """
        ranges = self._public_holiday_ranges() if ranges is None else ranges
        if ranges:
            self.env["hr.attendance"]._refresh_public_holiday_flags(ranges)
