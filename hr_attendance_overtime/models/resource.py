# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime

from pytz import timezone, utc

from odoo import api, fields, models

from odoo.addons.resource.models.resource import float_to_time


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    @api.model
    def default_get(self, fields):
        res = super(ResourceCalendar, self).default_get(fields)
        if "attendance_ids" in res:
            for _, _, attendance in res["attendance_ids"]:
                attendance["hour_check_in_from"] = attendance["hour_from"]
                attendance["hour_check_in_to"] = attendance["hour_from"]
                attendance["hour_check_out_from"] = attendance["hour_to"]
                attendance["hour_check_out_to"] = attendance["hour_to"]
        return res


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    _sql_constraints = [
        (
            "c-in_from_is_lower_than_c-in_to",
            "CHECK(hour_check_in_from <= hour_check_in_to)",
            "Check-in from should be lower or equals to check-in to.",
        ),
        (
            "c-out_from_is_lower_than_c-out_to",
            "CHECK(hour_check_out_from <= hour_check_out_to)",
            "Check-out from should be lower or equals to check-out to.",
        ),
        (
            "c-in_to_is_lower_than_c-out_from",
            "CHECK(hour_check_in_to <= hour_check_out_from)",
            "Check-in to should be lower or equals to check-out from.",
        ),
    ]

    hour_check_in_from = fields.Float(
        string="Work from check-in from",
        required=True,
        help="Check-in before will create attendance lines "
        "marked as overtime until this hour.",
        # set default to properly manage
        # line_section while generating two weeks calendar
        default=0,
    )
    hour_check_in_to = fields.Float(
        string="Work from check-in to",
        required=True,
        help="Check-in after will add a late reason on the attendance line.",
        # set default to properly manage
        # line_section while generating two weeks calendar
        default=0,
    )

    hour_check_out_from = fields.Float(
        string="Work to check-out from",
        required=True,
        help="Check-out before will add an early reason on attendance line.",
        # set default to properly manage
        # line_section while generating two weeks calendar
        default=0,
    )
    hour_check_out_to = fields.Float(
        string="Work to check-out to",
        required=True,
        help="Check-out after will create two attendances the last marked "
        "as overtime.",
        # set default to properly manage
        # line_section while generating two weeks calendar
        default=0,
    )

    @api.onchange("hour_check_in_from", "hour_check_in_to")
    def _onchange_check_in_hours(self):
        # avoid negative or after midnight
        self.hour_check_in_from = min(self.hour_check_in_from, 23.99)
        self.hour_check_in_from = max(self.hour_check_in_from, 0.0)
        self.hour_check_in_to = min(self.hour_check_in_to, 23.99)
        self.hour_check_in_to = max(self.hour_check_in_to, 0.0)

        # avoid wrong order
        self.hour_check_in_to = max(self.hour_check_in_to, self.hour_check_in_from)

    @api.onchange("hour_check_out_from", "hour_check_out_to")
    def _onchange_check_out_hours(self):
        # avoid negative or after midnight
        self.hour_check_out_from = min(self.hour_check_out_from, 23.99)
        self.hour_check_out_from = max(self.hour_check_out_from, 0.0)
        self.hour_check_out_to = min(self.hour_check_out_to, 23.99)
        self.hour_check_out_to = max(self.hour_check_out_to, 0.0)

        # avoid wrong order
        self.hour_check_out_to = max(self.hour_check_out_to, self.hour_check_out_from)

    def _copy_attendance_vals(self):
        res = super()._copy_attendance_vals()
        res.update(
            {
                "hour_check_in_from": self.hour_check_in_from,
                "hour_check_in_to": self.hour_check_in_to,
                "hour_check_out_from": self.hour_check_out_from,
                "hour_check_out_to": self.hour_check_out_to,
            }
        )
        return res

    def _get_datetime_from_field(self, dt_naive_utc, field_name):
        """return hour field in naïve utc datetime for the given day"""
        dt_tz = dt_naive_utc.replace(tzinfo=utc)
        tz = timezone(self.calendar_id.tz)
        dt_cal_tz = dt_tz.astimezone(tz)
        return (
            tz.localize(
                datetime.combine(
                    dt_cal_tz.date(), float_to_time(getattr(self, field_name))
                )
            )
            .astimezone(utc)
            .replace(tzinfo=None)
        )
