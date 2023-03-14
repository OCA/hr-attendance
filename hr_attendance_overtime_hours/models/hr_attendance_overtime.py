from odoo import models, fields, api
from datetime import datetime, time
import logging
_logger = logging.getLogger(__name__)


class HrAttendanceOvertime(models.Model):
    _inherit = 'hr.attendance.overtime'
    
    planned_hours = fields.Float(compute='_compute_planned_hours', store=True, readonly=True)
    worked_hours = fields.Float(compute='_compute_worked_hours', store=True, readonly=True)

    @api.depends('date')
    def _compute_planned_hours(self):
        for overtime in self:
            # Get work hours from calendar
            planned_hours = self.employee_id.resource_calendar_id.get_work_hours_count(
                datetime.combine(overtime.date, time.min),
                datetime.combine(overtime.date, time.max),
                True)
            overtime.planned_hours = planned_hours

    @api.depends('duration')
    def _compute_worked_hours(self):
        for overtime in self:
            # Get sum of attendance entries
            attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('check_in', '>=', datetime.combine(overtime.date, time.min)),
                ('check_out', '<=', datetime.combine(overtime.date, time.max)),
            ])
            overtime.worked_hours = sum(attendance_ids.mapped('worked_hours'))