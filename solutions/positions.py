import os
import numpy as np
import pandas as pd
from husfort.qutility import SFY, SFG, check_and_makedirs
from husfort.qinstruments import CInstruMgr, parse_instrument_from_contract
from typedef import CKey, CPos, EnumSigs, EnumPOSD


def convert_signal_to_positions(
        sig_date: str,
        sig_type: EnumSigs,
        signals_file_name_tmpl: str,
        positions_file_name_tmpl: str,
        signals_dir: str,
        positions_dir: str,
        allocated_equity: float,
        instru_mgr: CInstruMgr,
):
    sig_file = signals_file_name_tmpl.format(sig_date, sig_type.value)
    sig_path = os.path.join(signals_dir, sig_date[0:4], sig_date[4:6], sig_file)
    if not os.path.exists(sig_path):
        raise FileNotFoundError(sig_path)

    sig_data = pd.read_csv(sig_path)
    pos_data = sig_data[["contract", "weight", "close"]].copy()
    pos_data["total_equity"] = allocated_equity
    pos_data["allocated_equity"] = allocated_equity * pos_data["weight"]
    pos_data["instrument"] = pos_data["contract"].map(parse_instrument_from_contract)
    pos_data["multiplier"] = pos_data["instrument"].map(lambda z: instru_mgr.get_multiplier(z))
    pos_data["qty_raw"] = pos_data.apply(
        lambda z: z["allocated_equity"] / z["multiplier"] / z["close"],
        axis=1,
    )
    pos_data["quantity"] = pos_data["qty_raw"].round(0).abs().astype(int)
    pos_data["direction"] = pos_data["qty_raw"].map(lambda z: int(np.sign(z)))

    pos_file = positions_file_name_tmpl.format(sig_date, sig_type.value)
    check_and_makedirs(pos_d := os.path.join(positions_dir, sig_date[0:4], sig_date[4:6]))
    pos_path = os.path.join(pos_d, pos_file)
    pos_data.to_csv(pos_path, index=False, float_format="%.8f")
    print(f"[INF] Positions of {sig_date}-{sig_type.value} saved to {SFG(pos_path)}")
    return 0


def load_position_tqdb(
        sig_date: str,
        sig_type: EnumSigs,
        positions_file_name_tmpl: str,
        positions_dir: str,
) -> dict[CKey, CPos]:
    pos_file = positions_file_name_tmpl.format(sig_date, sig_type.value)
    pos_path = os.path.join(positions_dir, sig_date[0:4], sig_date[4:6], pos_file)
    if not os.path.exists(pos_path):
        print(f"[INF] {SFY(pos_path)} is not available")
        return {}

    pos_df = pd.read_csv(pos_path)
    res: dict[CKey, CPos] = {}
    for contract, direction, qty, close in zip(
            pos_df["contract"], pos_df["direction"], pos_df["quantity"], pos_df["close"]):
        if direction != 0:
            key = CKey(contract=contract, direction=EnumPOSD(direction))
            pos = CPos(key=key, qty=qty, base_price=close)
            res[key] = pos
    return res


def load_position_fuai(
        sig_date: str,
        sig_type: EnumSigs,
        positions_file_name_fuai_tmpl: str,
        positions_dir: str,
) -> dict[CKey, CPos]:
    pos_file = positions_file_name_fuai_tmpl.format(sig_date)
    pos_path = os.path.join(positions_dir, sig_date[0:4], sig_date[4:6], pos_file)
    if not os.path.exists(pos_path):
        print(f"[INF] {SFY(pos_path)} is not available")
        return {}

    if sig_type == EnumSigs.opn:
        account = "胡晓欧截面CTA开盘"
    elif sig_type == EnumSigs.cls:
        account = "胡晓欧截面CTA收盘"
    else:
        raise ValueError(f"Invalid sig_type ={sig_type}")

    pos_df = pd.read_excel(pos_path).set_index("合约").query(f"策略账户 == '{account}'")
    res: dict[CKey, CPos] = {}
    for contract, r in pos_df.iterrows():
        contract: str
        if (qty := r["买总持仓"]) > 0:
            key = CKey(contract=contract, direction=EnumPOSD.LNG)
            pos = CPos(key=key, qty=qty)
            res[key] = pos
        if (qty := r["卖总持仓"]) > 0:
            key = CKey(contract=contract, direction=EnumPOSD.SRT)
            pos = CPos(key=key, qty=qty)
            res[key] = pos
    return res
