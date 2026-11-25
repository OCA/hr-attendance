import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {ConnectionLostError, rpc} from "@web/core/network/rpc";
import {patch} from "@web/core/utils/patch";
import {signal} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.attendanceReasonRef = signal.ref();
        this.attendance_reason_param = "";
    },
    async signInOut() {
        this.attendance_reason_param = "";
        // Check if the reasons are required
        // and the employee has to select a reason
        if (this.state.employee?.show_reason_on_attendance_screen) {
            const select = this.attendanceReasonRef();
            const attendance_reason_id = select ? select.value : "0";
            if (
                this.state.employee.required_reason_on_attendance_screen &&
                attendance_reason_id === "0"
            ) {
                this.notification.add(_t("An attendance reason is required!"), {
                    title: _t("Please, select a reason!"),
                    type: "danger",
                });
                return false;
            }
            // Make sure that the attendance reason id is not 0 (be empty instead)
            this.attendance_reason_param =
                attendance_reason_id === "0" ? "" : attendance_reason_id;
        }
        return super.signInOut(...arguments);
    },
    async checking({latitude = false, longitude = false, checkInImage = null} = {}) {
        // Same as the original method, only adding the selected attendance
        // reason as parameter to the rpc call
        try {
            const employee = await rpc("/hr_attendance/systray_check_in_out", {
                latitude,
                longitude,
                check_in_image: checkInImage,
                attendance_reason_id: this.attendance_reason_param,
            });
            this._searchReadEmployeeFill(employee);
            this._foldAttendanceReview();
            if (employee?.notification?.message) {
                this.notification.add(employee.notification.message, {
                    type: employee.notification.type,
                });
            }
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                this.notification.add(
                    _t("Connection lost. Check in/out could not be recorded."),
                    {
                        title: _t("Attendance Error"),
                        type: "danger",
                        sticky: false,
                    }
                );
            } else {
                throw error;
            }
        } finally {
            this._attendanceInProgress = false;
        }
    },
});
