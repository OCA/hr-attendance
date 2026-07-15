import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";

patch(ActivityMenu.prototype, {
    _searchReadEmployeeFill() {
        super._searchReadEmployeeFill();
        // Expose the running-break state to the systray template.
        this.state.onBreak = Boolean(this.employee.on_break);
    },
    async toggleBreak() {
        // Start or end a break, then refresh the systray with the new state.
        this.employee = await rpc("/hr_attendance/toggle_break");
        this._searchReadEmployeeFill();
    },
});
