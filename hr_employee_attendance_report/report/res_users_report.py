from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
import pytz
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta, time


class ReportResUsers(models.AbstractModel):
    _name = 'report.hr_employee_attendance_report.res_users'
    _description = 'Attendance and leave report'

    def _daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def get_attendances(self, users):
        """Group attendances by user and day."""

        # Data mappings
        dates = {}
        attendances = {}
        summary = {}

        # Init statics
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        
        # Iterate on users
        for user in users:
            employee = user.employee_id
            hours_per_day = user.company_id.resource_calendar_id.hours_per_day

            # Get first and last day of last month
            tz = pytz.timezone(employee.tz or 'UTC')
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz + relativedelta(months=-1, day=1, hour=0, minute=0, second=0, microsecond=0)            
            end_tz = now_tz + relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Log time range
            dates[user.id] = {}
            dates[user.id]['start_date'] = start_tz
            dates[user.id]['end_date'] = end_tz

            # Get all leaves, attendances and overtime in range
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            end_naive = end_tz.astimezone(pytz.utc).replace(tzinfo=None)
            attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                '&',
                ('check_in', '<=', end_naive),
                ('check_out', '>=', start_naive),
            ])
            overtime_ids = self.env['hr.attendance.overtime'].search([
                ('employee_id', '=', employee.id),
                '&',
                ('date', '<=', end_naive),
                ('date', '>=', start_naive),
            ])
            leave_ids = self.env['resource.calendar.leaves'].search([
                ('calendar_id', '=', employee.resource_calendar_id.id),
                ('resource_id', '=', employee.resource_id.id),
                '|', ('date_from', '>=', start_tz), ('date_to', '<=', end_tz),
            ])

            # Update summary
            planned_hours = employee.resource_calendar_id.get_work_hours_count(start_naive, end_naive, True)
            leave_hours = sum(leave_ids.holiday_id.mapped('number_of_hours_display'))
            summary[user.id] = {
                'planned_hours': round(planned_hours, 2),
                'leave_hours': leave_hours,
                'worked_hours': round(sum(attendance_ids.mapped('worked_hours')), 2),
                'overtime': round(sum(overtime_ids.mapped('duration')), 2),
                'overtime_total': round(employee.total_overtime, 2),
            }

            # For each date in rage compute data
            attendances[user.id] = []
            for date in self._daterange(start_tz, end_tz):
                
                # Get work hours
                min_check_date = datetime.combine(date, time.min)
                max_check_date = datetime.combine(date, time.max)
                work_hours = employee.resource_calendar_id.get_work_hours_count(
                    min_check_date,
                    max_check_date,
                    True
                )

                # Get leave hours for this date
                date_naive = date.astimezone(pytz.utc).replace(tzinfo=None)
                active_leaves = leave_ids.filtered(lambda l: 
                    l.date_from < date_naive < l.date_to or
                    min_check_date <= l.date_from <= max_check_date or 
                    min_check_date <= l.date_to <= max_check_date
                )
                
                leave_hours = 0.0
                if active_leaves.holiday_id:
                    number_of_hours = active_leaves.holiday_id.number_of_hours_display
                    if number_of_hours > hours_per_day:
                        leave_hours = work_hours
                    else:
                        leave_hours = number_of_hours
                # _logger.warning([date, leave_ids[0].date_from, leave_ids[0].date_to, min_check_date, max_check_date, leave_hours])
                
                # Get attendance hours for this date
                worked_hours = sum(attendance_ids.filtered(lambda a: min_check_date < a.check_in < max_check_date).mapped('worked_hours'))

                # Get overtime hours for this date
                overtime = sum(overtime_ids.filtered(lambda o: o.date == date.date()).mapped('duration'))

                # Create data entry
                attendances[user.id].append({
                    'date': date,
                    'planned_hours': work_hours,
                    'leave_hours': round(leave_hours, 2),
                    'worked_hours': round(worked_hours, 2),                    
                    'overtime': round(overtime, 2),
                    'background_color': 'lightgrey' if work_hours == 0 else 'none'
                })

        return dates, attendances, summary

    def get_leave_allocations(self, users):
        """Get data on leave and allocations."""

        # Data mappings
        leave_allocations = {}

        # Init statics
        now = fields.Datetime.now()

        # Iterate on users
        for user in users:
            employee = user.employee_id
            
            # Get active allocations
            allocation_ids = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('date_to', '>=', now),
                ('date_from', '<=', now)
            ])

            leave_allocations[user.id] = allocation_ids

        return leave_allocations

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['res.users'].browse(docids)

        dates, attendances, summary = self.get_attendances(docs)
        leave_allocations = self.get_leave_allocations(docs)

        return {
            'doc_ids': docids,
            'doc_model': 'res.users',
            'docs': docs,
            'dates': dates,
            'attendances': attendances,            
            'summary': summary,
            'leave_allocations': leave_allocations
        }