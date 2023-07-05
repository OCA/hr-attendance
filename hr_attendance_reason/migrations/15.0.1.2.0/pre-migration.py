from openupgradelib import openupgrade

_field_renames = [
    (
        "res.company",
        "res_company",
        "show_reasons_on_attendance_screen",
        "show_reason_on_attendance_screen",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, "res_company", "show_reasons_on_attendance_screen"
    ):
        openupgrade.rename_fields(env, _field_renames)
