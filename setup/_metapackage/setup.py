import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-hr-attendance",
    description="Meta package for oca-hr-attendance Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-hr_attendance_autoclose',
        'odoo14-addon-hr_attendance_geolocation',
        'odoo14-addon-hr_attendance_hour_type_report',
        'odoo14-addon-hr_attendance_modification_tracking',
        'odoo14-addon-hr_attendance_overtime',
        'odoo14-addon-hr_attendance_reason',
        'odoo14-addon-hr_attendance_report_theoretical_time',
        'odoo14-addon-hr_attendance_rfid',
        'odoo14-addon-hr_attendance_sheet',
        'odoo14-addon-hr_attendance_validation',
        'odoo14-addon-hr_birthday_welcome_message',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
