# Copyright 2019 Creu Blanca
# Copyright 2021 Landoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models


class HrAttendance(models.Model):
    _name = "hr.attendance"
    _inherit = ["hr.attendance", "mail.thread"]

    employee_id = fields.Many2one(tracking=True)
    check_in = fields.Datetime(tracking=True)
    check_out = fields.Datetime(tracking=True)
    time_changed_manually = fields.Boolean(
        string="Time changed",
        default=False,
        readonly=True,
        help="This attendance has been manually changed by user. If attendance"
        " is created from form view, a 60 seconds tolerance will "
        "be applied.",
    )

    def _check_manual_time_change(self, check, val, current_value=None, now=None):
        if not val:
            return False
        if current_value:
            return True
        if not now:
            now = fields.Datetime.now()
        tolerance = timedelta(seconds=60)
        val_dt = fields.Datetime.to_datetime(val)
        return abs(val_dt - now) > tolerance

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()
        for vals in vals_list:
            for check in ["check_in", "check_out"]:
                if self._check_manual_time_change(check, vals.get(check), now=now):
                    vals["time_changed_manually"] = True
                    break
        return super().create(vals_list)

    def write(self, vals):
        now = fields.Datetime.now()
        for record in self:
            for check in ["check_in", "check_out"]:
                if check in vals:
                    current_value = getattr(record, check)
                    if record._check_manual_time_change(
                        check, vals.get(check), current_value=current_value, now=now
                    ):
                        record.time_changed_manually = True
        return super().write(vals)
