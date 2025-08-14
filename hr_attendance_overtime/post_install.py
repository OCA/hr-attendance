# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api


def set_week_checkin_checkout_hours_ranges(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    attendances = env["resource.calendar.attendance"].search([])
    for attendance in attendances:
        attendance.hour_check_in_from = attendance.hour_from
        attendance.hour_check_in_to = attendance.hour_from
        attendance.hour_check_out_from = attendance.hour_to
        attendance.hour_check_out_to = attendance.hour_to
