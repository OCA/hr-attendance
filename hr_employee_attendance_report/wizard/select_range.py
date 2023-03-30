import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class HREmployeeAttendanceReportSelectRange(models.TransientModel):

    _name = 'hr_employee_attendance_report.select_range'
    _description = 'Attendance and leave report range selector'

    date_from = fields.Date(string='From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_until = fields.Date(string='Until', required=True, default=lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],)

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        action = self.env.ref('hr_employee_attendance_report.res_users_report').report_action(None, data)
        return action
