import os
from husfort.qmails import CAgentEmail, CAttachmentText
from typedef import CAccountMail
from solutions.orders import parse_tm_from_sec_and_apm


def send_orders(
        account_mail: CAccountMail,
        sig_date: str,
        exe_date: str,
        sec_type: str,
        orders_file_name_tmpl: str,
        orders_dir: str,
        receivers: list[str],
):
    agent = CAgentEmail(
        mail_host=account_mail.host,
        mail_port=account_mail.port,
        mail_sender=account_mail.sender,
        mail_sender_pwd=account_mail.password,
    )
    d = os.path.join(orders_dir, sig_date[0:4], sig_date[4:6])
    if sec_type == "opn":
        tm_pm = parse_tm_from_sec_and_apm(sec_type, am_or_pm="pm")
        tm_am = parse_tm_from_sec_and_apm(sec_type, am_or_pm="am")
        attachments = [
            CAttachmentText(orders_file_name_tmpl.format(sig_date, sig_date, sec_type, "pm", tm_pm), d),
            CAttachmentText(orders_file_name_tmpl.format(sig_date, exe_date, sec_type, "am", tm_am), d),
        ]
    elif sec_type == "cls":
        tm = parse_tm_from_sec_and_apm(sec_type, am_or_pm="pm")
        attachments = [
            CAttachmentText(orders_file_name_tmpl.format(sig_date, exe_date, sec_type, "pm", tm), d),
        ]
    else:
        raise ValueError(f"Invalid sig_type: {sec_type}")

    agent.write(
        receivers=receivers,
        msg_subject=f"仿真交易指令-sig-{sig_date}-exe-{exe_date}-{sec_type}",
        msg_body="指令见附件",
        attachments=attachments,
    )
    agent.send()
    return 0
