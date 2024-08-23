# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import api, models

from . import attendance_data

_logger = logging.getLogger(__name__)


class ReportHrEmployee(models.AbstractModel):
    _name = "report.hr_employee_attendance_report.hr_employee"
    _description = "Attendance and leave report"

    @api.model
    def _get_report_values(self, docids, data=None):
        return attendance_data._get_report_values(self, docids, data, self._name)
