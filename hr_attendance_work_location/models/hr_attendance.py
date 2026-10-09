# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# 1 degree of latitude ≈ 111,320 meters (varies slightly with latitude)
_METERS_PER_DEGREE = 111_320.0


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    company_id = fields.Many2one(
        "res.company",
        related="employee_id.company_id",
        store=True,
        depends=["employee_id"],
    )

    in_work_location_id = fields.Many2one(
        "hr.work.location",
        string="Check-in Work Location",
        help="Work location at check-in time",
        compute="_compute_work_locations",
        store=True,
        readonly=False,
        domain="[('company_id', '=', company_id)]",
        tracking=True,
    )

    out_work_location_id = fields.Many2one(
        "hr.work.location",
        string="Check-out Work Location",
        help="Work location at check-out time",
        compute="_compute_work_locations",
        store=True,
        readonly=False,
        domain="[('company_id', '=', company_id)]",
        tracking=True,
    )

    @api.constrains("employee_id", "in_work_location_id", "out_work_location_id")
    def _check_work_locations(self):
        for attendance in self:
            if (
                attendance.in_work_location_id
                and attendance.in_work_location_id.company_id != attendance.company_id
            ):
                raise ValidationError(
                    _(
                        "Check-in work location must belong to the same company "
                        "as the employee."
                    )
                )
            if (
                attendance.out_work_location_id
                and attendance.out_work_location_id.company_id != attendance.company_id
            ):
                raise ValidationError(
                    _(
                        "Check-out work location must belong to the same company "
                        "as the employee."
                    )
                )

    def _find_work_location_by_coords(
        self, work_locations, latitude, longitude, tol=0.001
    ):
        """Return the id of the closest work location within *tol* degrees,
        or False when no candidate is found.

        Candidates are first filtered to a bounding box of ±tol.
        Among those, the closest one is selected using the flat-earth
        approximation corrected for longitude convergence:

            d² = Δlat² + (Δlon · cos(lat_rad))²
        """
        lat_rad = math.radians(latitude)
        candidates = work_locations.filtered(
            lambda loc: abs(loc.address_id.partner_latitude - latitude) <= tol
            and abs(loc.address_id.partner_longitude - longitude) <= tol
        )
        if not candidates:
            return False
        closest = candidates.sorted(
            key=lambda loc: (loc.address_id.partner_latitude - latitude) ** 2
            + ((loc.address_id.partner_longitude - longitude) * math.cos(lat_rad)) ** 2
        )[:1]
        return closest.id or False

    @api.depends("in_latitude", "in_longitude", "out_latitude", "out_longitude")
    def _compute_work_locations(self):
        available_work_locations = self.env["hr.work.location"].search(
            [("exclude_from_attendance", "=", False)]
        )
        for attendance in self:
            tolerance_meters = attendance.company_id.geo_tolerance_meters
            if not tolerance_meters:
                continue
            tolerance_degrees = tolerance_meters / _METERS_PER_DEGREE
            company_work_locations = available_work_locations.filtered(
                lambda loc, att=attendance: loc.company_id == att.company_id
            )
            if (
                not attendance.in_work_location_id
                and attendance.in_latitude
                and attendance.in_longitude
            ):
                attendance.in_work_location_id = self._find_work_location_by_coords(
                    company_work_locations,
                    attendance.in_latitude,
                    attendance.in_longitude,
                    tol=tolerance_degrees,
                )
            if (
                attendance.check_out
                and not attendance.out_work_location_id
                and attendance.out_latitude
                and attendance.out_longitude
            ):
                attendance.out_work_location_id = self._find_work_location_by_coords(
                    company_work_locations,
                    attendance.out_latitude,
                    attendance.out_longitude,
                    tol=tolerance_degrees,
                )
