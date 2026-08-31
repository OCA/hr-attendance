# Copyright 2026 Tecnativa - Víctor Martínez
from odoo import fields, models


class HrAattendance(models.Model):
    _inherit = "hr.attendance"

    def _get_worked_hours_in_range(self, start_dt, end_dt):
        # It is important to define the appropriate context keys so that the value is
        # as expected.
        from_date = fields.Datetime.context_timestamp(self, start_dt).date()
        to_date = fields.Datetime.context_timestamp(self, end_dt).date()
        self = self.with_context(
            flexible_hours_from_date=from_date,
            flexible_hours_to_date=to_date,
        )
        return super()._get_worked_hours_in_range(start_dt, end_dt)
