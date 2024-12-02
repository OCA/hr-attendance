/* global navigator */

import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {isIosApp} from "@web/core/browser/feature_detection";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";
import {useRef} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.attendance_reason = useRef("attendance_reason");
    },
    async signInOut() {
        let attendance_reason_param = "";
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
                this.notification.add(_t("An attendance reason is required!"), {
                    title: _t("Please, select a reason!"),
                    type: "danger",
                });
                return false;
            }
            // Make sure that the attendance reason id is not 0 (be empty instead)
            attendance_reason_param =
                attendance_reason_id === "0" ? "" : attendance_reason_id;
        }

        // Overwrite super method because we need to add the attendance reason to the rpc calls
        this.dropdown.close();
        if (isIosApp()) {
            await rpc("/hr_attendance/systray_check_in_out", {
                // CHANGE: add attendance reason as parameter to rpc call
                attendance_reason_id: attendance_reason_param,
            });
            await this.searchReadEmployee();
        } else {
            // IOS app lacks permissions to call `getCurrentPosition`
            navigator.geolocation.getCurrentPosition(
                async ({coords: {latitude, longitude}}) => {
                    await rpc("/hr_attendance/systray_check_in_out", {
                        latitude,
                        longitude,
                        // CHANGE: add attendance reason as parameter to rpc call
                        attendance_reason_id: attendance_reason_param,
                    });
                    await this.searchReadEmployee();
                },
                async () => {
                    await rpc("/hr_attendance/systray_check_in_out", {
                        // CHANGE: add attendance reason as parameter to rpc call
                        attendance_reason_id: attendance_reason_param,
                    });
                    await this.searchReadEmployee();
                },
                {
                    enableHighAccuracy: true,
                }
            );
        }
    },
});
