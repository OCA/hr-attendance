# Copyright 2019 Creu Blanca
# Copyright 2020 Landoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields, models


class HrAttendance(models.Model):
    _name = "hr.attendance"
    _inherit = ["hr.attendance", "mail.thread"]

    employee_id = fields.Many2one(tracking=True)
    check_in = fields.Datetime(tracking=True)
    check_out = fields.Datetime(tracking=True)
    time_changed_manually = fields.Boolean(
        string="Time changed",
        compute="_compute_time_changed_manually",
        default=False,
        store=True,
        help="This attendance has been manually changed by user. If attendance"
        " is created from form view, a 60 seconds tolerance will "
        "be applied.",
    )

    @api.depends("message_ids.tracking_value_ids")
    def _compute_time_changed_manually(self):
        for record in self:
            if not record.time_changed_manually:
                # For manual attendance, tolerance to consider it acceptable
                tolerance = timedelta(seconds=60)
                for track in record.message_ids.with_user(SUPERUSER_ID).mapped(
                    "tracking_value_ids"
                ):
                    if track.field in ["check_in", "check_out"]:
                        # Attendance created from kiosk or check-in/check-out
                        if track.old_value_datetime:
                            record.time_changed_manually = True
                        # Attendance created in form view, if check-in and
                        # check-out are in admitted tolerance,
                        # they will not be considered "manually changed"
                        else:
                            diff = abs(
                                track.new_value_datetime - track.mail_message_id.date
                            )
                            if diff > tolerance:
                                record.time_changed_manually = True

    @api.model
    def create(self, vals):
        tolerance = timedelta(seconds=60)
        now = fields.Datetime.now()
        for check in ["check_in", "check_out"]:
            if (
                vals.get(check, False)
                and abs(fields.Datetime.from_string(vals.get(check)) - now) > tolerance
            ):
                vals.update({"time_changed_manually": True})
                break
        return super().create(vals)
