def post_init_hook(env):
    companies = env["res.company"].search([])
    # That field on model res.company is created, and the existing records are
    # updated accordingly, before the field's default record is created.
    # Sequence from the Odoo log:
    # > odoo.modules.loading: Loading module hr_attendance_reason
    # > odoo.registry: module hr_attendance_reason: creating or updating database tables
    # > odoo.modules.loading: loading hr_attendance_reason/data/hr_attendance_reason.xml
    # Hence, setting it here.
    companies.reason_for_attendance_absence_detection = env.ref(
        "hr_attendance_reason.attendance_reason_absence_detection"
    )
