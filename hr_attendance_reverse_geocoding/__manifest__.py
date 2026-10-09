# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "HR Attendance Reverse Geocoding",
    "summary": "Convert GPS coordinates from attendances to readable addresses",
    "version": "16.0.1.0.1",
    "category": "Human Resources/Attendances",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Binhex Systems Solutions S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "hr_attendance",
        "hr_attendance_geolocation",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter_data.xml",
        "views/hr_attendance_views.xml",
        "views/res_config_settings_views.xml",
        "views/hr_attendance_geocode_cache_views.xml",
    ],
    "installable": True,
    "application": False,
}
