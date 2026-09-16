from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class IDSecureHistoricalSyncWizard(models.TransientModel):
    """Wizard to recover access events from a specific date range.

    Use this when the regular sync was interrupted and events were
    missed.  It calls the iDSecure API with date filters and a higher
    limit so that older events are fetched.
    """

    _name = "idsecure.historical.sync.wizard"
    _description = "iDSecure Historical Sync"

    device_id = fields.Many2one(
        "idsecure.device",
        string="Device",
        required=True,
        default=lambda self: self.env.context.get("active_id"),
    )
    date_from = fields.Datetime(
        string="From",
        required=True,
        default=lambda self: fields.Datetime.now() - timedelta(days=4),
    )
    date_to = fields.Datetime(
        string="To",
        required=True,
        default=lambda self: fields.Datetime.now(),
    )
    limit = fields.Integer(
        string="Max Events",
        default=5000,
        help="Maximum number of events to fetch from the device.",
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from >= rec.date_to:
                raise ValidationError(_("'From' date must be before 'To' date."))

    def action_sync(self):
        self.ensure_one()
        self.device_id.action_sync_access_events(
            limit=self.limit,
            initial_date=self.date_from,
            final_date=self.date_to,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Historical Sync Complete"),
                "message": _(
                    "Events between %(start)s and %(end)s have been synced. "
                    "Check the device log for details.",
                    start=fields.Datetime.to_string(self.date_from),
                    end=fields.Datetime.to_string(self.date_to),
                ),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
