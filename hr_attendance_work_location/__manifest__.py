# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "HR Attendance - Work Location Tracking",
    "version": "17.0.1.2.0",
    "category": "Human Resources",
    "license": "AGPL-3",
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "summary": "Track work location at check-in and check-out in HR Attendance records",
    "depends": ["base_geolocalize", "hr_attendance"],
    "data": [
        "views/hr_work_location_views.xml",
        "views/hr_attendance_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
