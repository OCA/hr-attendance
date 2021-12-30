from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hr_attendance_compensatory_leave_type_id = fields.Many2one(
        "hr.leave.type",
        "Overtime compensatory leave type",
        config_parameter="hr_attendance_validation.leave_type_id",
        required=True,
        default=lambda self: self.env.ref("hr_holidays.holiday_status_comp"),
        help="Compensatory leave type used while validate weekly attendance sheet.",
    )
