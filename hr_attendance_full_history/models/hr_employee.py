# Copyright 2026 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def action_open_last_month_attendances(self):
        result = super().action_open_last_month_attendances()
        # Drop the fixed current month range on check_in...
        result["domain"] = [leaf for leaf in result["domain"] if leaf[0] != "check_in"]
        # ...and restrict to the current month with a removable filter instead
        result["context"]["search_default_check_in_filter"] = True
        return result
