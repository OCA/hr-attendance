# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import _, fields, models

from ..services.geocoding_service import GeocodingService

_logger = logging.getLogger(__name__)

GEOCODE_STATUS = [
    ("pending", "Pending"),
    ("done", "Done"),
    ("error", "Error"),
]
position_fields = {
    "check_in_latitude",
    "check_in_longitude",
    "check_out_latitude",
    "check_out_longitude",
}


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_address = fields.Char(string="Reverse Geocoding Check-in", readonly=True)
    check_out_address = fields.Char(string="Reverse Geocoding Check-out", readonly=True)
    check_in_geocode_status = fields.Selection(
        selection=GEOCODE_STATUS,
        string="Geocoding Status Check-in",
        readonly=True,
        copy=False,
    )
    check_out_geocode_status = fields.Selection(
        selection=GEOCODE_STATUS,
        string="Geocoding Status Check-out",
        readonly=True,
        copy=False,
    )
    check_in_geocode_provider = fields.Char(
        string="Check-in Provider",
        readonly=True,
        copy=False,
    )
    check_out_geocode_provider = fields.Char(
        string="Check-out Provider",
        readonly=True,
        copy=False,
    )

    check_in_map_url = fields.Char(
        string="Check-in Map URL",
        readonly=True,
        copy=False,
    )
    check_out_map_url = fields.Char(
        string="Check-out Map URL",
        readonly=True,
        copy=False,
    )
    check_in_geocode_error = fields.Text(
        string="Check-in Geocoding Error",
        readonly=True,
        copy=False,
    )
    check_out_geocode_error = fields.Text(
        string="Check-out Geocoding Error",
        readonly=True,
        copy=False,
    )

    def write(self, vals):
        result = super().write(vals)
        if position_fields & vals.keys():
            for record in self:
                record._enqueue_reverse_geocoding(vals)

        return result

    def _enqueue_reverse_geocoding(self, vals=None):
        self.ensure_one()
        vals_keys = vals.keys()
        if any("check_in" in key for key in vals_keys):
            prefix = "check_in"
        elif any("check_out" in key for key in vals_keys):
            prefix = "check_out"
        else:
            return

        description = _("Reverse geocoding %(prefix)s: Attendance %(self.id)s")
        self._mark_pending(prefix)
        self.with_delay(description=description)._resolve_geocoding(prefix, vals)

    def _mark_pending(self, prefix):
        self.ensure_one()
        self.update(
            {
                f"{prefix}_geocode_status": "pending",
                f"{prefix}_address": False,
                f"{prefix}_geocode_provider": False,
                f"{prefix}_geocode_error": False,
            }
        )

    def _resolve_geocoding(self, prefix, vals):
        """
        Resolve the coordinates for the specified prefix
        and save the result to the record.

        :param prefix: str - 'check_in' or 'check_out'
        """
        self.ensure_one()
        try:
            service = GeocodingService(self.env)
            result = service.get_address(
                vals[f"{prefix}_latitude"], vals[f"{prefix}_longitude"]
            )

            self.sudo().update(
                {
                    f"{prefix}_address": result["address"],
                    f"{prefix}_geocode_status": "done",
                    f"{prefix}_geocode_provider": result["provider"],
                    f"{prefix}_map_url": result.get("map_url", ""),
                    f"{prefix}_geocode_error": False,
                }
            )

        except Exception as e:
            error_msg = str(e)
            self.sudo().update(
                {
                    f"{prefix}_geocode_status": "error",
                    f"{prefix}_geocode_error": error_msg,
                }
            )
