from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
import pytz
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta, time
from odoo.osv import expression

from . import attendance_data

class ReportHrEmployee(models.AbstractModel):
    _name = 'report.hr_employee_attendance_report.hr_employee'
    _description = 'Attendance and leave report'


    @api.model
    def _get_report_values(self, docids, data=None):
        return attendance_data._get_report_values(self, docids, data, self._name)
