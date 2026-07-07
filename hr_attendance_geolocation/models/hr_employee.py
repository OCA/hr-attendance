# Copyright 2019 ForgeFlow S.L.
# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self, geo_information=None):
        geo_information = dict(geo_information or {})
        latitude = geo_information.get("latitude", self.env.context.get("latitude"))
        longitude = geo_information.get("longitude", self.env.context.get("longitude"))

        res = super()._attendance_action_change(geo_information=geo_information or None)
        if latitude and longitude:
            if res and not res.check_out:
                res.write(
                    {
                        "check_in_latitude": latitude,
                        "check_in_longitude": longitude,
                    }
                )
            elif res:
                res.write(
                    {
                        "check_out_latitude": latitude,
                        "check_out_longitude": longitude,
                    }
                )
        return res
