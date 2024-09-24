# Copyright 2024 Binhex - Adasat Torres de León.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_attendance_image_capture = fields.Boolean(
        string="Image Capture",
        implied_group="hr_attendance_webcam.group_hr_attendance_image_capture",
    )
