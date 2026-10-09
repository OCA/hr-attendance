/** @odoo-module **/

import {Component, useState} from "@odoo/owl";

export class KioskWorkLocation extends Component {
    setup() {
        this.state = useState({
            selectedWorkLocationId: this.props.defaultWorkLocationId || false,
        });
    }

    onWorkLocationChange(ev) {
        this.state.selectedWorkLocationId = ev.target.value
            ? parseInt(ev.target.value, 10)
            : false;
    }

    onConfirm() {
        this.props.onConfirm(this.state.selectedWorkLocationId);
    }

    onCancel() {
        this.props.onCancel();
    }
}

KioskWorkLocation.template = "hr_attendance_work_location.kiosk_work_location";
