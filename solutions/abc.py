import os
import pandas as pd
from typing import Literal
from qtools_sxzq.qwidgets import SFY
from qtools_sxzq.qwidgets import parse_instrument_from_contract
from typedef import CKey, CPos, CTrade, COrder
from solutions.instruments import CInstruMgr


def load_position(sig_date: str, sec_type: Literal["opn", "cls"], position_file_dir: str) -> dict[CKey, CPos]:
    pos_file = f"positions_{sig_date}_{sec_type}.csv.gz"
    pos_path = os.path.join(position_file_dir, sig_date[0:4], sig_date[4:6], pos_file)
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


def cal_trades_from_pos(
        this_pos_grp: dict[CKey, CPos],
        prev_pos_grp: dict[CKey, CPos],
) -> list[CTrade]:
    res: list[CTrade] = []
    for pos_key, prev_pos in prev_pos_grp.items():
        this_pos = this_pos_grp.get(pos_key, CPos(key=pos_key, qty=0))
        trade = this_pos.cal_trade_from_another(another=prev_pos)
        res.append(trade)
    for pos_key, this_pos in this_pos_grp.items():
        if pos_key not in prev_pos_grp:
            prev_pos = CPos(key=pos_key, qty=0)
            trade = this_pos.cal_trade_from_another(another=prev_pos)
            res.append(trade)
    return res


def split_trades(trades: list[CTrade], instru_mgr: CInstruMgr) -> tuple[list[CTrade], list[CTrade]]:
    prev_trades: list[CTrade] = []
    this_trades: list[CTrade] = []
    for trade in trades:
        instru = parse_instrument_from_contract(contract_id=trade.key.contract)
        if instru_mgr.has_ngt(instru):
            prev_trades.append(trade)
        else:
            this_trades.append(trade)
    return prev_trades, this_trades


def gen_trades_at_opn(
        this_sig_date: str,
        prev_sig_date: str,
        position_file_dir: str,
        instru_mgr: CInstruMgr,
) -> tuple[list[CTrade], list[CTrade]]:
    this_pos_grp = load_position(sig_date=this_sig_date, sec_type="opn", position_file_dir=position_file_dir)
    prev_pos_grp = load_position(sig_date=prev_sig_date, sec_type="opn", position_file_dir=position_file_dir)
    trades = cal_trades_from_pos(this_pos_grp=this_pos_grp, prev_pos_grp=prev_pos_grp)
    pm_trades, am_trades = split_trades(trades=trades, instru_mgr=instru_mgr)
    return pm_trades, am_trades


def gen_trades_at_cls(
        this_sig_date: str,
        prev_sig_date: str,
        position_file_dir: str,
) -> list[CTrade]:
    this_pos_grp = load_position(sig_date=this_sig_date, sec_type="cls", position_file_dir=position_file_dir)
    prev_pos_grp = load_position(sig_date=prev_sig_date, sec_type="cls", position_file_dir=position_file_dir)
    trades = cal_trades_from_pos(this_pos_grp=this_pos_grp, prev_pos_grp=prev_pos_grp)
    return trades


def save_trades_for_orders(
        trades: list[CTrade],
        sec_type: Literal["opn", "cls"],
        orders_dir: str,
        instru_mgr: CInstruMgr,
):
    orders: list[COrder] = []
    for trade in trades:
        if trade.qty > 0:
            instru = parse_instrument_from_contract(contract_id=trade.key.contract)
            order = COrder(
                Exchange=instru_mgr.get_exchange(instru=instru),
                Product=instru,
                Instrument=trade.key.contract,
                Direction=trade.direction,
                OfstFlag=trade.offsetFlag,
                VolumeTotal=trade.qty,
            )
            orders.append(order)
