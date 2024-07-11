# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class HrContractHistory(models.Model):
    _inherit = "hr.contract.history"

    def action_update_overtime(self):
        return self.mapped("contract_ids").action_update_overtime()
