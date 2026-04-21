# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class HrContractHistory(models.Model):
    _inherit = "hr.contract.history"

    def action_update_overtime(self):
        for record in self:
            all_contracts = record.contract_ids.sorted("date_start", reverse=False)
            valid_contracts = all_contracts.filtered(
                lambda c: c.state in {"open", "close"}
            )
            for contract in valid_contracts:
                other_contracts = all_contracts - contract
                # Reorganize Leaves
                other_contracts.resource_calendar_id.transfer_leaves_to(
                    contract.resource_calendar_id,
                    resources=contract.employee_id.resource_id,
                    from_date=contract.date_start,
                )
        # Update Overtime
        self.contract_ids.action_update_overtime()
