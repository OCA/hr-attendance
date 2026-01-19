# Copyright 2026 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime

import freezegun

from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def action_open_last_month_attendances(self):
        # Using freezegun to predict the domain leaf we have to drop
        with freezegun.freeze_time(datetime.min):
            result = super().action_open_last_month_attendances()
            # Drop the starting date domain
            result["domain"].remove(("check_in", ">=", datetime.min))
        # Restrict them with a removable filter instead
        result["context"]["search_default_filter_this_month"] = True
        return result
