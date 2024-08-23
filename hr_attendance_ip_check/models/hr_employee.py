# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import ipaddress
import logging

from odoo import _, exceptions, fields, models
from odoo.http import request
from odoo.tools import config

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    attendance_cidr_ids = fields.Many2many("attendance.cidr", ondelete="restrict")

    def _attendance_ip_check(self):
        """Return if client ip is not in totp cidrs."""
        test_enable = config["test_enable"]
        # Get remote ip
        if test_enable:
            ip_address = ipaddress.IPv4Address("127.0.0.1")
        else:
            ip_address = ipaddress.IPv4Address(
                request.httprequest.environ["REMOTE_ADDR"]
            )

        # Get cidrs from employees
        employee_cidrs = self.sudo().attendance_cidr_ids

        # Get single check cidrs
        allowed_cidrs = employee_cidrs.filtered("single_check")[:1]

        # Combine global and employee cidrs
        if not allowed_cidrs:
            allowed_cidrs = self.env["attendance.cidr"].search(
                [("employee_ids", "=", False)]
            )
            allowed_cidrs += employee_cidrs

        # Chech if ip is in allowed_cidrs
        in_cidr = any(
            ip_address in cidr
            for cidr in allowed_cidrs.mapped(lambda r: ipaddress.IPv4Network(r.cidr))
        )

        # Raise exception if there is a cidr list and the client ip is not in cidr
        if allowed_cidrs and not in_cidr:
            raise exceptions.ValidationError(
                _(
                    "Not allowed to create new attendance record for "
                    "%(empl_name)s, the client ip is not in the "
                    "list of allowed ip networks."
                )
                % {
                    "empl_name": self.name,
                }
            )
