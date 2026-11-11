import math

from odoo import _, fields, models
from odoo.exceptions import UserError


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


class HREmployee(models.Model):
    _inherit = "hr.employee"

    bypass_geolocation_check = fields.Boolean(
        string="Ignore geolocation restrictions",
        default=False,
        help="If checked, this employee can clock in/out from any location.",
    )

    def _employee_allowed_locations(self):
        self.ensure_one()
        Location = self.env["hr.attendance.location"]
        return Location.search([])

    def _is_inside_any_allowed_location(self, lat, lon):
        self.ensure_one()

        if self.bypass_geolocation_check:
            return True, None

        if lat is False or lon is False:
            return False, None

        zones = self._employee_allowed_locations()

        if not zones and not self.env["hr.attendance.location"].search([]):
            return True, None
        for z in zones:
            d = _haversine_m(lat, lon, z.latitude, z.longitude)
            if d <= max(1, z.radius_m):
                return True, z
        return False, None

    def attendance_action_change(self):
        for emp in self:
            lat = getattr(emp, "last_attendance_latitude", False) or getattr(
                emp, "last_known_latitude", False
            )
            lon = getattr(emp, "last_attendance_longitude", False) or getattr(
                emp, "last_known_longitude", False
            )
            ok, _zone = emp._is_inside_any_allowed_location(lat, lon)
            if not ok:
                raise UserError(
                    _(
                        "You are outside an authorized area for clocking in. "
                        "Create a new area or go to an authorized zone."
                    )
                )
        return super().attendance_action_change()
