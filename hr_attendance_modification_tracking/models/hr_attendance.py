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

    @api.model_create_multi
    def create(self, vals_list):
        tolerance = timedelta(seconds=60)
        now = fields.Datetime.now()
        for vals in vals_list:
            for check in ["check_in", "check_out"]:
                if (
                    vals.get(check, False)
                    and abs(fields.Datetime.from_string(vals.get(check)) - now)
                    > tolerance
                ):
                    vals.update({"time_changed_manually": True})
                    break
        return super().create(vals_list)

    def write(self, vals):
        tolerance = timedelta(seconds=60)
        now = fields.Datetime.now()
        for record in self:
            for check in ["check_in", "check_out"]:
                if vals.get(check, False):
                    if getattr(record, check, False):
                        record.time_changed_manually = True
                    else:
                        check_str = vals.get(check)
                        diff = abs(fields.Datetime.from_string(check_str) - now)
                        if diff > tolerance:
                            record.time_changed_manually = True
        return super().write(vals)
