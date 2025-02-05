import os
import numpy as np
import pandas as pd
from typing import Literal
from husfort.qutility import SFY
from husfort.qinstruments import CInstruMgr, parse_instrument_from_contract
from typedef import CKey, CPos


def convert_signal_to_positions(
        sig_date: str,
        sig_type: Literal["opn", "cls"],
        signals_file_name_tmpl: str,
        positions_file_name_tmpl: str,
        signals_dir: str,
        positions_dir: str,
        allocated_equity: float,
        instru_mgr: CInstruMgr,
):
    sig_file = signals_file_name_tmpl.format(sig_date, sig_type)
    sig_path = os.path.join(signals_dir, sig_file[0:4], sig_date[4:6], sig_file)
    if not os.path.exists(sig_path):
        raise FileNotFoundError(sig_path)

    sig_data = pd.read_csv(sig_path)
    pos_data = sig_data[["contract", "weight"]].copy()
    pos_data["total_equity"] = allocated_equity
    pos_data["allocated_equity"] = allocated_equity * pos_data["weight"]
    pos_data["instrument"] = pos_data["contract"].map(parse_instrument_from_contract)
    pos_data["multiplier"] = pos_data["instrument"].map(lambda z: instru_mgr.get_multiplier(z))
    pos_data["qty_raw"] = pos_data.apply(
        lambda z: z["allocated_equity"] / z["multiplier"] / z["close"],
        axis=1,
    )
    pos_data["quantity"] = pos_data["qty_raw"].round(0).abs()
    pos_data["direction"] = pos_data["qty_raw"].map(lambda z: np.sign(z))

    pos_file = positions_file_name_tmpl.format(sig_date, sig_type)
    pos_path = os.path.join(positions_dir, sig_date[0:4], sig_date[4:6], pos_file)
    pos_data.to_csv(pos_path, index=False, float_format="%.8f")
    return 0


def load_position(
        sig_date: str,
        sig_type: Literal["opn", "cls"],
        positions_file_name_tmpl: str,
        positions_dir: str,
) -> dict[CKey, CPos]:
    pos_file = positions_file_name_tmpl.format(sig_date, sig_type)
    pos_path = os.path.join(positions_dir, sig_date[0:4], sig_date[4:6], pos_file)
    if os.path.exists(pos_path):
        print(f"[INF] {SFY(pos_path)} is not available")
        return {}

    pos_df = pd.read_csv(pos_path)
    res: dict[CKey, CPos] = {}
    for contract, direction, qty in zip(pos_df["contract"], pos_df["direction"], pos_df["quantity"]):
        key = CKey(contract=contract, direction=direction)
        pos = CPos(key=key, qty=qty)
        res[key] = pos
    return res
