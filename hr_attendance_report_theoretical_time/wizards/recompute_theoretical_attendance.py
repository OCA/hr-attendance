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

    def _action_recompute(self, attendances):
        """This method allows other modules to extend it to perform other actions
        and/or execute other methods compute from the corresponding attendances."""
        attendances._compute_theoretical_hours()

    def action_recompute(self):
        self.ensure_one()
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "in", self.employee_ids.ids),
                ("check_in", ">=", self.date_from),
                ("check_out", "<=", self.date_to),
            ]
        )
        self._action_recompute(attendances)
        return {"type": "ir.actions.act_window_close"}
