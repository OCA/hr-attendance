# Copyright (C) 2021 thingsintouch.com
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "HR Attendance Reason RFID",
    "version": "13.0.1.0.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "thingsintouch.com, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr_attendance_reason",
        "hr_attendance_rfid"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_reason_view.xml",
    ],
}
