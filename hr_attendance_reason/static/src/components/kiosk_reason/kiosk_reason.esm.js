import {Component, signal, t, useProps} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

export class KioskReason extends Component {
    static template = "hr_attendance_reason.KioskReason";

    props = useProps({
        employeeData: t.object(),
        reasons: t.array().optional(),
        pin_code: t.or([t.string(), t.boolean()]).optional(),
        onReasonConfirm: t.function(),
        onClickBack: t.function(),
    });

    attendanceReasonRef = signal.ref();

    setup() {
        this.notification = useService("notification");
        this.checkedIn = this.props.employeeData.attendance_state === "checked_in";
    }

    async onClickSelectReason() {
        const attendance_reason_id = this.attendanceReasonRef().value;
        if (
            this.props.employeeData.required_reason_on_attendance_screen &&
            attendance_reason_id === "0"
        ) {
            this.notification.add(_t("An attendance reason is required!"), {
                title: _t("Please, select a reason"),
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
