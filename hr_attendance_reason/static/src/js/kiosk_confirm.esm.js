/** @odoo-module **/
import KioskConfirm from "hr_attendance.kiosk_confirm";
import {_t} from "web.core";

const superSignInOut =
    KioskConfirm.prototype.events["click .o_hr_attendance_sign_in_out_icon"];
const superPinPadButton =
    KioskConfirm.prototype.events["click .o_hr_attendance_pin_pad_button_ok"];

KioskConfirm.include({
    events: Object.assign({}, KioskConfirm.prototype.events, {
        "click .o_hr_attendance_sign_in_out_icon": function () {
            this.update_attendance(superSignInOut);
        },
        "click .o_hr_attendance_pin_pad_button_ok": function () {
            this.update_attendance(superPinPadButton);
        },
    }),
    willStart: async function () {
        await this._super();
        await this._rpc({
            model: "hr.employee",
            method: "search_read",
            args: [
                [["user_id", "=", this.getSession().uid]],
                [
                    "show_reason_on_attendance_screen",
                    "required_reason_on_attendance_screen",
                ],
            ],
        }).then((res) => {
            this.employee = res.length && res[0];
        });
        await this._rpc({
            model: "hr.attendance.reason",
            method: "search_read",
            fields: ["name", "action_type"],
            domain: [["show_on_attendance_screen", "=", true]],
        }).then((reasons) => {
            this.reasons = reasons;
        });
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
    update_attendance: function (event_func) {
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
            event_func = event_func.bind(this);
            event_func();
        }
    },
});
