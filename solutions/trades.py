from typing import Literal
from husfort.qinstruments import parse_instrument_from_contract, CInstruMgr
from typedef import CKey, CPos, CTrade, COrder
from solutions.positions import load_position


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
        instru = parse_instrument_from_contract(contract=trade.key.contract)
        if instru_mgr.has_ngt_sec(instru):
            prev_trades.append(trade)
        else:
            this_trades.append(trade)
    return prev_trades, this_trades


def gen_trades_at_opn(
        this_sig_date: str,
        prev_sig_date: str,
        positions_file_name_tmpl: str,
        positions_dir: str,
        instru_mgr: CInstruMgr,
) -> tuple[list[CTrade], list[CTrade]]:
    this_pos_grp = load_position(this_sig_date, "opn", positions_file_name_tmpl, positions_dir)
    prev_pos_grp = load_position(prev_sig_date, "opn", positions_file_name_tmpl, positions_dir)
    trades = cal_trades_from_pos(this_pos_grp=this_pos_grp, prev_pos_grp=prev_pos_grp)
    pm_trades, am_trades = split_trades(trades=trades, instru_mgr=instru_mgr)
    return pm_trades, am_trades


def gen_trades_at_cls(
        this_sig_date: str,
        prev_sig_date: str,
        positions_file_name_tmpl,
        positions_dir: str,
) -> list[CTrade]:
    this_pos_grp = load_position(this_sig_date, "cls", positions_file_name_tmpl, positions_dir)
    prev_pos_grp = load_position(prev_sig_date, "cls", positions_file_name_tmpl, positions_dir)
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
            instru = parse_instrument_from_contract(contract=trade.key.contract)
            order = COrder(
                Exchange=instru_mgr.get_exchange(instrumentId=instru),
                Product=instru,
                Instrument=trade.key.contract,
                Direction=trade.op_direction,
                OfstFlag=trade.offsetFlag,
                VolumeTotal=trade.qty,
            )
            orders.append(order)
