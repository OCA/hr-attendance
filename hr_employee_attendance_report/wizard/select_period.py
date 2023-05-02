import time
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class HREmployeeAttendanceReportSelectPeriod(models.TransientModel):

    _name = 'hr_employee_attendance_report.select_period'
    _description = 'Attendance and leave report period selector'

    date_from = fields.Date(string='From', required=True, default=lambda *a: str(date.today() + relativedelta(months=-1, day=1)))
    date_until = fields.Date(string='Until', required=True, default=lambda *a: str(date.today() + relativedelta(day=1) - timedelta(days=1)))

    def print_report(self, download_only=False):
        self.ensure_one()
        context = self.env.context        

        # Check if wizards is called from user or employee view
        active_model = context.get('active_model')
        report = 'hr_employee_attendance_report.hr_employee_report'
        if active_model == 'res.users':
            report = 'hr_employee_attendance_report.res_users_report'

        [data] = self.read()        
        action = self.env.ref(report).with_context(download_only=download_only).report_action(None, data)
        return action

    def download_report(self):
        return self.print_report(download_only=True)
