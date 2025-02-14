import os
import pandas as pd
from husfort.qutility import check_and_makedirs, SFG, SFY
from husfort.qinstruments import parse_instrument_from_contract, CInstruMgr
from typedef import CKey, CPos, CTrade, EnumSigs, EnumPOSD, EnumOFFSET
from solutions.positions import load_position


def cal_trades_from_pos(
        this_pos_grp: dict[CKey, CPos],
        prev_pos_grp: dict[CKey, CPos],
) -> list[CTrade]:
    res: list[CTrade] = []
    for pos_key, prev_pos in prev_pos_grp.items():
        this_pos = this_pos_grp.get(pos_key, CPos(key=pos_key, qty=0))
        trade = this_pos.cal_trade_from_another(another=prev_pos)
        res.append(trade) if trade.qty > 0 else None
    for pos_key, this_pos in this_pos_grp.items():
        if pos_key not in prev_pos_grp:
            prev_pos = CPos(key=pos_key, qty=0)
            trade = this_pos.cal_trade_from_another(another=prev_pos)
            res.append(trade) if trade.qty > 0 else None
    return res


def gen_trades(
        this_sig_date: str,
        prev_sig_date: str,
        sig_type: EnumSigs,
        positions_file_name_tmpl,
        positions_dir: str,
) -> list[CTrade]:
    this_pos_grp = load_position(this_sig_date, sig_type, positions_file_name_tmpl, positions_dir)
    prev_pos_grp = load_position(prev_sig_date, sig_type, positions_file_name_tmpl, positions_dir)
    trades = cal_trades_from_pos(this_pos_grp=this_pos_grp, prev_pos_grp=prev_pos_grp)
    return trades


def save_trades(
        trades: list[CTrade],
        sig_date: str,
        sig_type: EnumSigs,
        trades_file_name_tmpl: str,
        trades_dir: str,
):
    trades_data: list[dict] = []
    for trade in trades:
        trades_data.append(trade.to_dict())
    check_and_makedirs(d := os.path.join(trades_dir, sig_date[0:4], sig_date[4:6]))
    trades_file = trades_file_name_tmpl.format(sig_date, sig_type.value)
    trades_path = os.path.join(d, trades_file)
    if trades_data:
        df = pd.DataFrame(data=trades_data).sort_values(by="contract")
        # print(df)
    else:
        df = pd.DataFrame(columns=CTrade.names())
        print(f"[INF] There are no trades available for {SFY(sig_date)}-{SFY(sig_type.value)}.")
    df.to_csv(trades_path, index=False)
    print(f"[INF] Trades of {sig_date}-{sig_type.value} are saved to {SFG(trades_path)}")
    return 0


def load_trades(
        sig_date: str,
        sig_type: EnumSigs,
        trades_file_name_tmpl: str,
        trades_dir: str,
) -> list[CTrade]:
    trades_file = trades_file_name_tmpl.format(sig_date, sig_type.value)
    trades_path = os.path.join(trades_dir, sig_date[0:4], sig_date[4:6], trades_file)
    trades_data = pd.read_csv(trades_path, header=0)
    trades: list[CTrade] = []
    for _, r in trades_data.iterrows():
        key = CKey(contract=r["contract"], direction=EnumPOSD(r["direction"]))
        trade = CTrade(
            key=key,
            offset=EnumOFFSET(r["offset"]),
            qty=r["qty"],
            base_price=r["base_price"],
            order_price=r["order_price"],
        )
        trades.append(trade)
    return trades


def split_trades(trades: list[CTrade], instru_mgr: CInstruMgr) -> tuple[list[CTrade], list[CTrade]]:
    opn_pm_trades: list[CTrade] = []
    opn_am_trades: list[CTrade] = []
    for trade in trades:
        instru = parse_instrument_from_contract(contract=trade.key.contract)
        if instru_mgr.has_ngt_sec(instru):
            opn_pm_trades.append(trade)
        else:
            opn_am_trades.append(trade)
    return opn_pm_trades, opn_am_trades
