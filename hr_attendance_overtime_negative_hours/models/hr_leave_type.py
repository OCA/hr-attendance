from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    @api.model
    def get_days_all_request(self):
        """Always return the extra hours leave type."""
        extra_hours_time_off_type = self.env.ref('hr_holidays_attendance.holiday_status_extra_hours', raise_if_not_found=False)
        leave_types = sorted(self.search([]).filtered(lambda x: (x.virtual_remaining_leaves > 0 or x.max_leaves or (x == extra_hours_time_off_type))), key=self._model_sorting_key, reverse=True)
        return [lt._get_days_request() for lt in leave_types]