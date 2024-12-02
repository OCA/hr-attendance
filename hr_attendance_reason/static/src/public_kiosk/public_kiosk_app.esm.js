import {KioskReason} from "@hr_attendance_reason/components/kiosk_reason/kiosk_reason.esm";
import {patch} from "@web/core/utils/patch";
import PublicKiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import {rpc} from "@web/core/network/rpc";
import {_t} from "@web/core/l10n/translation";

patch(PublicKiosk.kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.getKioskReasonSettings();
        this.show_attendance_reason_screen = true;
        this.attendance_reason_id = "";
    },
    switchDisplay(screen) {
        if (screen === "reason") {
            this.state.active_display = screen;
            return;
        }
        return super.switchDisplay(screen);
    },
    async onManualSelection(employeeId, enteredPin) {
        // Check if is need to show the reason screen
        if (
            this.show_reason_on_attendance_screen &&
            this.show_attendance_reason_screen
        ) {
            const employee = await rpc("/hr_attendance_reason/get_reasons", {
                token: this.props.token,
                employee_id: employeeId,
                pin_code: enteredPin,
            });
            if (employee && employee.employee_name) {
                this.employeeData = employee;
                this.reasons = employee.reasons;
                this.pin_code = enteredPin;
                return this.switchDisplay("reason");
            }
        }

        // Prepare selected reason for rpc call
        const attendance_reason_param =
            this.attendance_reason_id === "0" ? "" : this.attendance_reason_id;

        // Overwrite super method because we need to add the attendance reason to the rpc calls
        const result = await this.makeRpcWithGeolocation("manual_selection", {
            token: this.props.token,
            employee_id: employeeId,
            pin_code: enteredPin,
            attendance_reason_id: attendance_reason_param,
        });
        if (result && result.attendance) {
            this.employeeData = result;
            this.switchDisplay("greet");
        } else if (enteredPin) {
            this.displayNotification(_t("Wrong Pin"));
        }
    },
    async getKioskReasonSettings() {
        const result = await rpc("/hr_attendance_reason/reason_settings", {
            token: this.props.token,
        });
        this.show_reason_on_attendance_screen = result.show_reason_on_attendance_screen;
    },
    async onReasonSelection(employeeId, pin_code, attendance_reason_id) {
        // Set the show_attendance_reason_screen
        // for when onManualSelection is called,
        // the 'reason' screen will not be displayed again.
        this.show_attendance_reason_screen = false;
        this.attendance_reason_id = attendance_reason_id;
        await this.onManualSelection(employeeId, pin_code);
        this.show_attendance_reason_screen = true;
    },
});

PublicKiosk.kioskAttendanceApp.components = {
    ...PublicKiosk.kioskAttendanceApp.components,
    KioskReason,
};
