import os
from typing import Literal
from paramiko import SSHClient
from scp import SCPClient
from husfort.qutility import SFY, SFG
from husfort.qutility import check_and_makedirs
from typedef import CHost


def scp_from_remote(
        host: CHost,
        remote_path: str,
        local_path: str,
        recursive: bool = False
):
    with SSHClient() as ssh:
        ssh.load_system_host_keys()
        ssh.connect(hostname=host.hostname, username=host.username, port=host.port)
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(remote_path=remote_path, local_path=local_path, recursive=recursive)
            print(f"[INF] copy {SFY(remote_path)} to {SFG(local_path)}")
    return 0


def download_signals_from(
        sig_date: str,
        sig_type: Literal["opn", "cls"],
        signals_file_name_tmpl: str,
        src_signals_dir: str,
        dst_signals_dir: str,
        host: CHost,
):
    check_and_makedirs(dst_dir := os.path.join(dst_signals_dir, sig_date[0:4], sig_date[4:6]))
    target_file = signals_file_name_tmpl.format(sig_date, sig_type)

    remote_path = f"{src_signals_dir}/{sig_date[0:4]}/{sig_date[4:6]}/{target_file}"
    local_path = os.path.join(dst_dir, target_file)
    scp_from_remote(
        host=host,
        remote_path=remote_path,
        local_path=local_path,
        recursive=False,
    )
    return 0
