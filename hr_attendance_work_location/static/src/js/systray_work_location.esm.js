/** @odoo-module **/

import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {ConnectionLostError} from "@web/core/network/rpc_service";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {useState} from "@odoo/owl";

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.company = useService("company");
        this.wlState = useState({
            mode: "automatic",
            locations: [],
            selectedId: false,
        });
        this._loadWorkLocations();
    },

    async _loadWorkLocations() {
        const companyId = this.company.currentCompany.id;
        const [companyData] = await this.orm.read(
            "res.company",
            [companyId],
            ["work_location_mode", "manual_work_location_id"]
        );
        if (companyData) {
            this.wlState.mode = companyData.work_location_mode;
            this.wlState.selectedId = companyData.manual_work_location_id
                ? companyData.manual_work_location_id[0]
                : false;
        }
        if (this.wlState.mode === "manual") {
            this.wlState.locations = await this.orm.searchRead(
                "hr.work.location",
                [
                    ["company_id", "=", companyId],
                    ["exclude_from_attendance", "=", false],
                ],
                ["id", "name"]
            );
        }
    },

    onWorkLocationChange(ev) {
        this.wlState.selectedId = ev.target.value
            ? parseInt(ev.target.value, 10)
            : false;
    },

    async checking(latitude = false, longitude = false) {
        try {
            await this.rpc("/hr_attendance/systray_check_in_out", {
                latitude,
                longitude,
                work_location_id: this.wlState.selectedId || false,
            });
            this.searchReadEmployee();
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
