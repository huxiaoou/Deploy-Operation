from husfort.qinstruments import CInstruMgr, parse_instrument_from_contract
from typedef import CTrade, COrder


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


def convert_trades_to_orders(
        trades: list[CTrade],
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
