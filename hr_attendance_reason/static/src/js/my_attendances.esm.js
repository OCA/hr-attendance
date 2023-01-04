/** @odoo-module **/

odoo.define("hr_attendance_reason.my_attendances", function (require) {
    var MyAttendances = require("hr_attendance.my_attendances");
    var core = require("web.core");
    var _t = core._t;

    MyAttendances.include({
        willStart: function () {
            const prom = this.call(
                "hr_attendance_reason_service",
                "updateUserContextAsync",
                {
                    extra_fields: [
                        "show_reasons_on_attendance_screen",
                        "required_reason_on_attendance_screen",
                    ],
                }
            );
            return Promise.all([prom, this._super.apply(this, arguments)]);
        },
        init: function () {
            this._super.apply(this, arguments);
            this.reasons = this.getAttendanceReasons();
        },
        getAttendanceReasons: function () {
            this.reasons = [];
            this._rpc({
                model: "hr.attendance.reason",
                method: "search_read",
                fields: ["name", "action_type"],
                domain: [["show_on_attendance_screen", "=", true]],
            }).then((reasons) => {
                this.reasons = reasons;
            });
            return this.reasons;
        },
        update_attendance: function () {
            const attendance_reason_id = parseInt(
                this.$(".o_hr_attendance_reason").val(),
                0
            );
            if (
                attendance_reason_id === 0 &&
                this.employee.required_reason_on_attendance_screen
            ) {
                this.do_warn(_t("Please, select a reason"));
            } else {
                const prom = this.call(
                    "hr_attendance_reason_service",
                    "updateUserContextAsync",
                    {attendance_reason_id: attendance_reason_id}
                );
                return Promise.all([prom, this._super.apply(this, arguments)]);
            }
        },
    });
});
