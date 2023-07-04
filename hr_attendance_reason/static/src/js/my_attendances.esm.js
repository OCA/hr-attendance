/** @odoo-module **/
import MyAttendances from "hr_attendance.my_attendances";
import session from "web.session";
import {_t} from "web.core";

MyAttendances.include({
    willStart: function () {
        Object.assign(session.user_context, {
            extra_fields: [
                "show_reason_on_attendance_screen",
                "required_reason_on_attendance_screen",
            ],
        });
        return this._super();
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
    // This override is the way to inject into the context of an enclosed rpc call.
    _rpc: function () {
        const [{model, method, context}] = arguments;
        if (!context) {
            return this._super(...arguments);
        }
        if (model === "hr.employee" && method === "search_read") {
            context.extra_fields = [
                "show_reason_on_attendance_screen",
                "required_reason_on_attendance_screen",
            ];
        }
        if (this.attendance_reason_id) {
            context.attendance_reason_id = this.attendance_reason_id;
        }
        return this._super(...arguments);
    },
    update_attendance: function () {
        this.attendance_reason_id = parseInt(
            this.$(".o_hr_attendance_reason").val(),
            0
        );
        if (
            this.attendance_reason_id === 0 &&
            this.employee.required_reason_on_attendance_screen
        ) {
            this.displayNotification({
                title: _t("Please, select a reason"),
                type: "danger",
            });
        } else {
            this._super();
        }
    },
});
