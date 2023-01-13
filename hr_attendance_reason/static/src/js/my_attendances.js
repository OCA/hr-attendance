odoo.define("hr_attendance_reason.my_attendances", function(require) {
    "use strict";

    var MyAttendances = require("hr_attendance.my_attendances");
    const session = require("web.session");
    var core = require("web.core");
    var _t = core._t;

    MyAttendances.include({
        willStart: function() {
            Object.assign(session.user_context, {
                extra_fields: ["show_reasons_on_attendance_screen"],
            });
            return this._super();
        },
        init: function() {
            this._super.apply(this, arguments);
            this.reasons = this.getAttendanceReasons();
        },
        getAttendanceReasons: function() {
            this.reasons = [];
            this._rpc({
                model: "hr.attendance.reason",
                method: "search_read",
                fields: ["name", "action_type"],
                domain: [["show_on_attendance_screen", "=", true]],
            }).then(reasons => {
                this.reasons = reasons;
            });
            return this.reasons;
        },
        update_attendance: function() {
            const attendance_reason_id = parseInt(
                this.$(".o_hr_attendance_reason").val(),
                0
            );
            Object.assign(session.user_context, {
                attendance_reason_id: attendance_reason_id,
            });
            if (attendance_reason_id === 0) {
                this.do_warn(_t("Please, select a reason"));
            } else {
                this._super();
            }
        },
    });
});
