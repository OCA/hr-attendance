# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrWorkLocation(models.Model):
    _inherit = "hr.work.location"

    exclude_from_attendance = fields.Boolean(
        default=False,
        help=(
            "When set, this work location will be ignored for automatic "
            "assignment to attendances based on GPS coordinates."
        ),
    )
