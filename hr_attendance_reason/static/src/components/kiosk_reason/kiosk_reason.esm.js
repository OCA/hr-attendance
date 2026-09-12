import {Component, useRef} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

export class KioskReason extends Component {
    setup() {
        this.notification = useService("notification");
        this.checkedIn = this.props.employeeData.attendance_state === "checked_in";
        this.attendance_reason = useRef("attendance_reason");
    }

    async onClickSelectReason() {
        const attendance_reason_id = this.attendance_reason.el.value;
        if (
            this.props.employeeData.required_reason_on_attendance_screen &&
            attendance_reason_id === "0"
        ) {
            this.notification.add(_t("An attendance reason is required!"), {
                title: _t("Please, select a reason!"),
                type: "danger",
            });
            return false;
        }
        await this.props.onReasonConfirm(
            this.props.employeeData.id,
            this.props.pin_code,
            attendance_reason_id
        );
    }
}

KioskReason.props = {
    employeeData: {type: Object},
    onClickBack: {type: Function},
    onPinConfirm: {type: Function},
};

KioskReason.template = "hr_attendance_reason.KioskReason";
