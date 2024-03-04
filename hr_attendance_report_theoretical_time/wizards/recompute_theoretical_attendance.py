# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class RecomputeTheoreticalAttendance(models.TransientModel):
    _name = "recompute.theoretical.attendance"
    _description = "Recompute Employees Attendances"

    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        required=True,
        string="Employees",
        help="Recompute these employees attendances",
    )
    date_from = fields.Datetime(
        string="From", required=True, help="Recompute attendances from this date"
    )
    date_to = fields.Datetime(
        string="To", required=True, help="Recompute attendances up to this date"
    )

    def action_recompute(self):
        self.ensure_one()
        # First we need to manage leaves (as they are linked to the calendar
        # and need to be removed and added back to be correctly processed)
        leave_model = self.env["hr.leave"]
        leaves = leave_model.search([
            ("employee_id", "in", self.employee_ids.ids),
            # Here we need to include leaves even partially contained in
            # the date range. Otherwise leaves won't be retrieved.
            ("date_from", ">=", self.date_from),
            ("date_from", "<=", self.date_to),
        ])
        leaves._remove_resource_leave()
        leaves._create_resource_leave()
        leaves._check_theoretical_hours()
        # Then we can process remaining attendances
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "in", self.employee_ids.ids),
                ("check_in", ">=", self.date_from),
                ("check_out", "<=", self.date_to),
            ]
        )
        attendances._compute_theoretical_hours()
        return {"type": "ir.actions.act_window_close"}
