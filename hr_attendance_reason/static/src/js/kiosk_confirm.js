odoo.define("hr_attendance_reason.kiosk_confirm", function(require) {
    "use strict";
    const KioskConfirm = require("hr_attendance.kiosk_confirm");
    const session = require("web.session");
    const core = require("web.core");
    const _t = core._t;
    const superSignInOut =
        KioskConfirm.prototype.events["click .o_hr_attendance_sign_in_out_icon"];
    const superPinPadButton =
        KioskConfirm.prototype.events["click .o_hr_attendance_pin_pad_button_ok"];
    KioskConfirm.include({
        events: Object.assign({}, KioskConfirm.prototype.events, {
            "click .o_hr_attendance_sign_in_out_icon": function() {
                this.update_attendance(superSignInOut);
            },
            "click .o_hr_attendance_pin_pad_button_ok": function() {
                this.update_attendance(superPinPadButton);
            },
        }),
        willStart: async function() {
            await this._super();
            await this._rpc({
                model: "hr.employee",
                method: "search_read",
                args: [
                    [["user_id", "=", this.getSession().uid]],
                    ["show_reasons_on_attendance_screen"],
                ],
            }).then(res => {
                this.employee = res.length && res[0];
            });
            await this._rpc({
                model: "hr.attendance.reason",
                method: "search_read",
                fields: ["name", "action_type"],
                domain: [["show_on_attendance_screen", "=", true]],
            }).then(reasons => {
                this.reasons = reasons;
            });
        },
        update_attendance: function(event_func) {
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
                event_func = event_func.bind(this);
                event_func();
            }
        },
    });
});
