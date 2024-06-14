# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import ipaddress
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AttendanceCidr(models.Model):
    _name = "attendance.cidr"
    _description = "Allowed Attendance CIDR"
    _rec_name = "cidr"

    employee_ids = fields.Many2many(
        "hr.employee", string="Employees", ondelete="restrict"
    )
    cidr = fields.Char(string="CIDR")
    single_check = fields.Boolean(
        help="Check if CIDR should no be combined with other CIDRs."
    )

    @api.constrains("cidr")
    def _validate_cidr(self):
        for rec in self:
            try:
                ipaddress.IPv4Network(rec.cidr)
            except Exception:
                raise ValidationError(_("This is not a valid CIDR.")) from None
