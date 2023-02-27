from odoo import _, api, fields, models, exceptions
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)
import ipaddress


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    attendance_cidr_ids = fields.Many2many('attendance.cidr', ondelete='restrict')

    def _attendance_ip_check(self):
        """Return if client ip is not in totp cidrs."""

        # Get remote ip
        ip_address = ipaddress.IPv4Address(request.httprequest.environ['REMOTE_ADDR'])
        
        # Get cidrs from employee
        employee_cidrs = self.sudo().attendance_cidr_ids
        
        # Get single check cidrs
        allowed_cidrs = employee_cidrs.filtered('single_check')[:1]

        # Combine global and employee cidrs
        if not allowed_cidrs:
            allowed_cidrs = self.env['attendance.cidr'].search([('employee_ids', '=', False)])
            allowed_cidrs += employee_cidrs
                
        # Chech if ip is in allowed_cidrs
        in_cidr = any(ip_address in cidr for cidr in allowed_cidrs.mapped(lambda r: ipaddress.IPv4Network(r.cidr)))

        # Raise exception if there is a cidr list and the client ip is not in cidr 
        if allowed_cidrs and not in_cidr:
            raise exceptions.ValidationError(_('Not allowed to create new attendance record for %(empl_name)s, the client ip is not in the list of allowed ip networks.') % {
                'empl_name': self.name,
            })
