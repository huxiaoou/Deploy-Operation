import os
from husfort.qutility import check_and_makedirs
from husfort.qremote import CHost, scp_from_remote
from typedef import EnumSigs


def download_signals_from(
        sig_date: str,
        sig_type: EnumSigs,
        signals_file_name_tmpl: str,
        src_signals_dir: str,
        dst_signals_dir: str,
        host: CHost,
):
    check_and_makedirs(dst_dir := os.path.join(dst_signals_dir, sig_date[0:4], sig_date[4:6]))
    target_file = signals_file_name_tmpl.format(sig_date, sig_type.value)

    remote_path = f"{src_signals_dir}/{sig_date[0:4]}/{sig_date[4:6]}/{target_file}"
    local_path = os.path.join(dst_dir, target_file)
    scp_from_remote(
        host=host,
        remote_path=remote_path,
        local_path=local_path,
        recursive=False,
    )
    return 0
