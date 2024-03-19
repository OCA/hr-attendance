# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time

import pytz

from odoo import models


class Employee(models.Model):
    _inherit = "hr.employee"

    def _get_work_intervals_batch(self, dt_from, dt_to):
        intervals = []

        tz = pytz.timezone(self.tz or "UTC")
        for contract in self._get_contracts(dt_from, dt_to, states=["open", "close"]):
            start = datetime.combine(contract.date_start, time.min)
            start = max(dt_from, tz.localize(start).astimezone(pytz.UTC))

            if contract.date_end:
                end = datetime.combine(contract.date_end, time.max)
                end = min(dt_to, tz.localize(end).astimezone(pytz.UTC))
            else:
                end = dt_to

            intervals.extend(
                contract.resource_calendar_id._work_intervals_batch(start, end)[False]
            )

        return intervals
