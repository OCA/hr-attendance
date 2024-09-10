# Copyright 2023 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    ignored_in_attendance_validation = fields.Boolean()
    is_compensatory = fields.Boolean(
        help="If check, taken leaves are displayed in hr attendance validation analysis report."
    )
