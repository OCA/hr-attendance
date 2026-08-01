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
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "assets": {
        "web.assets_backend": [
            "hr_attendance_work_location/static/src/**/*",
        ],
        "hr_attendance.assets_public_attendance": [
            "hr_attendance_work_location/static/src/js/kiosk_work_location_component.esm.js",
            "hr_attendance_work_location/static/src/xml/kiosk_work_location.xml",
            "hr_attendance_work_location/static/src/js/kiosk_work_location.esm.js",
            "hr_attendance_work_location/static/src/xml/kiosk_greeting_extension.xml",
        ],
    },
}
