# Copyright 2023 - thingsintouch.com
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "HR Attendance RFID Log",
    "version": "13.0.1.0.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "thingsintouch.com, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["hr_attendance_rfid"],
    "data": [
        "data/ir_cron_data.xml",
        "data/system_parameters.xml",
        "security/groups.xml",
        "security/ir.model.access.csv",
        # "data/ir_rule.xml",
        "views/hr_attendance_log_view.xml",
        "wizards/hr_rfid_log_assign_employee.xml"
    ],
}
