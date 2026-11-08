import {KioskBreak} from "@hr_attendance_break/components/kiosk_break/kiosk_break.esm";
import PublicKiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";

patch(PublicKiosk.kioskAttendanceApp.prototype, {
    switchDisplay(screen) {
        if (screen === "break_choice") {
            this.state.active_display = screen;
            return;
        }
        return super.switchDisplay(screen);
    },
    async onManualSelection(employeeId, enteredPin) {
        // When a checked-in employee identifies themselves, offer a break
        // instead of checking them straight out.
        if (!this._skipBreakChoice) {
            const state = await rpc("/hr_attendance_break/employee_state", {
                token: this.props.token,
                employee_id: employeeId,
                pin_code: enteredPin,
            });
            if (state && state.checked_in) {
                this._breakEmployeeId = employeeId;
                this._breakPin = enteredPin;
                this.breakData = {
                    employee_name: state.employee_name,
                    on_break: state.on_break,
                };
                return this.switchDisplay("break_choice");
            }
        }
        this._skipBreakChoice = false;
        return super.onManualSelection(employeeId, enteredPin);
    },
    async onKioskToggleBreak() {
        const result = await rpc("/hr_attendance_break/toggle_break_kiosk", {
            token: this.props.token,
            employee_id: this._breakEmployeeId,
            pin_code: this._breakPin,
        });
        if (result && result.attendance) {
            this.employeeData = result;
            this.switchDisplay("greet");
        } else {
            this.switchDisplay("main");
        }
    },
    async onKioskBreakCheckout() {
        // Bypass the break choice and run the normal check-out.
        this._skipBreakChoice = true;
        await this.onManualSelection(this._breakEmployeeId, this._breakPin);
    },
});

PublicKiosk.kioskAttendanceApp.components = {
    ...PublicKiosk.kioskAttendanceApp.components,
    KioskBreak,
};
