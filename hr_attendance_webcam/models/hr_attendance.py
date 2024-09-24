# Copyright 2024 Binhex - Adasat Torres de León.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class HrAttendanceMod(models.Model):
    _inherit = "hr.attendance"

    image_check_in = fields.Binary("Check-in image", attachment=True)
    image_check_out = fields.Binary("Check-out image", attachment=True)
