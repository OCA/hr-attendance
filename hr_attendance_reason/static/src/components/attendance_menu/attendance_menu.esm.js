/** @odoo-module */

import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {_lt} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {useRef} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.reasons = this.getAttendanceReasons();
        this.attendance_reason = useRef("attendance_reason");
    },
    async getAttendanceReasons() {
        this.reasons = [];
        await this.orm
            .call("hr.attendance.reason", "search_read", [], {
                fields: ["name", "action_type"],
                domain: [["show_on_attendance_screen", "=", true]],
            })
            .then((reasons) => {
                this.reasons = reasons;
            });
        return this.reasons;
    },
    async signInOut() {
        // Check if the reasons are required
        // and the employee has to select a reason
        if (this.employee.show_reason_on_attendance_screen) {
            const attendance_reason_id = this.attendance_reason.el
                ? this.attendance_reason.el.value
                : "0";
            if (
                this.employee.required_reason_on_attendance_screen &&
                attendance_reason_id === "0"
            ) {
                this.notification.add(_lt("An attendance reason is required!"), {
                    title: _lt("Please, select a reason!"),
                    type: "danger",
                });
                return false;
            }
        }
        return super.signInOut();
    },
});
