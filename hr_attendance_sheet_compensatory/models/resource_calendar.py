# Copyright 2021 Pierre Verkest
# Copyright 2023 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    total_hours = fields.Float(
        "Total calendar hours",
        compute="_compute_total_hours",
        help="Total theoretical hours used to compute compensatory days",
    )

    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = sum(
                rec.attendance_ids.mapped(lambda att: att.hour_to - att.hour_from)
            )
