# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# Part of ForgeFlow. See LICENSE file for full copyright and licensing details.

from odoo import http

from odoo.addons.hr_attendance.controllers.main import HrAttendance as HrAttendanceBase


class HrAttendance(HrAttendanceBase):
    # Inherited route to filter employees with kiosk access
    @http.route("/hr_attendance/employees_infos", type="json", auth="public")
    def employees_infos(self, token, limit, offset, domain):
        domain = domain + [("allow_kiosk_access", "=", True)]
        return super().employees_infos(token, limit, offset, domain)
