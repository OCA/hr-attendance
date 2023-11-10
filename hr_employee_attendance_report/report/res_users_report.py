import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

from . import attendance_data


class ReportResUsers(models.AbstractModel):
    _name = "report.hr_employee_attendance_report.res_users"
    _description = "Attendance and leave report"

    @api.model
    def _get_report_values(self, docids, data=None):
        return attendance_data._get_report_values(self, docids, data, self._name)
