# Copyright 2024 Binhex - Adasat Torres de León.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self):
        res = super()._attendance_action_change()
        image = self.env.context.get("image", False)
        if self.attendance_state == "checked_in" and image:
            res.write({"image_check_in": image})
        if self.attendance_state == "checked_out" and image:
            res.write({"image_check_out": image})
        return res
