import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-hr-attendance",
    description="Meta package for oca-hr-attendance Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-hr_attendance_autoclose',
        'odoo13-addon-hr_attendance_geolocation',
        'odoo13-addon-hr_attendance_modification_tracking',
        'odoo13-addon-hr_attendance_reason',
        'odoo13-addon-hr_attendance_report_theoretical_time',
        'odoo13-addon-hr_attendance_rfid',
        'odoo13-addon-hr_attendance_user_list',
        'odoo13-addon-hr_birthday_welcome_message',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
