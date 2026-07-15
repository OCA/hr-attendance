import {Component} from "@odoo/owl";

export class KioskBreak extends Component {}

KioskBreak.props = {
    employeeData: {type: Object},
    onToggleBreak: {type: Function},
    onCheckout: {type: Function},
    onClickBack: {type: Function},
};

KioskBreak.template = "hr_attendance_break.KioskBreak";
