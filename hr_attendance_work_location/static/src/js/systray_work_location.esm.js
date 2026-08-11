/** @odoo-module **/
// Copyright 2026 Binhex
// License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {patch} from "@web/core/utils/patch";
import {rpcService} from "@web/core/network/rpc_service";
import {useService} from "@web/core/utils/hooks";
import {useState} from "@odoo/owl";

// Selected work location for the NEXT systray check-in/out call. Synced from
// wlState.selectedId and injected by the rpc wrapper below. Module-scope state
// survives the dropdown closing, unlike DOM reads.
let selectedWorkLocationId = false;

const originalStart = rpcService.start;
rpcService.start = function (env) {
    const originalRpc = originalStart(env);
    return function rpc(route, params = {}, settings = {}) {
        if (route === "/hr_attendance/systray_check_in_out" && selectedWorkLocationId) {
            params.work_location_id = selectedWorkLocationId;
        }
        return originalRpc(route, params, settings);
    };
};

patch(ActivityMenu.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.company = useService("company");
        this.wlState = useState({
            mode: "automatic",
            locations: [],
            selectedId: false,
            defaultId: false,
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
            this.wlState.defaultId = companyData.manual_work_location_id
                ? companyData.manual_work_location_id[0]
                : false;
            this.wlState.selectedId = this.wlState.defaultId;
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
        selectedWorkLocationId = this.wlState.selectedId;
    },

    async searchReadEmployee() {
        await super.searchReadEmployee(...arguments);
        if (!this.wlState) {
            return;
        }
        if (
            this.state.checkedIn &&
            this.employee &&
            this.employee.in_work_location_id
        ) {
            this.wlState.selectedId = this.employee.in_work_location_id;
        } else if (!this.state.checkedIn) {
            this.wlState.selectedId = this.wlState.defaultId || false;
        }
        selectedWorkLocationId = this.wlState.selectedId;
    },

    onWorkLocationChange(ev) {
        this.wlState.selectedId = ev.target.value
            ? parseInt(ev.target.value, 10)
            : false;
        selectedWorkLocationId = this.wlState.selectedId;
    },
});
