import os
import numpy as np
import pandas as pd
from typing import Literal
from dataclasses import asdict
from husfort.qutility import check_and_makedirs, SFG, SFY
from husfort.qinstruments import CInstruMgr, parse_instrument_from_contract
from typedef import CTrade, COrder, CAccountTianqin, CPriceBounds
from solutions.md import req_md_last_price_tianqin, req_md_trade_date_wind


def convert_trades_to_orders(
        trades: list[CTrade],
        instru_mgr: CInstruMgr,
        drift: float,
        strategy: str,
) -> list[COrder]:
    orders: list[COrder] = []
    for trade in trades:
        if trade.qty > 0:
            instru = parse_instrument_from_contract(contract=trade.key.contract)
            mini_spread = instru_mgr.get_mini_spread(instru)
            trade.update_order_price(drift, mini_spread)
            order = COrder(
                Exchange=instru_mgr.get_exchange(instrumentId=instru),
                Product=instru,
                Instrument=trade.key.contract,
                Direction=trade.op_direction,
                Price=trade.order_price,
                OfstFlag=trade.offsetFlag,
                VolumeTotal=trade.qty,
                Strategy=strategy,
            )
            orders.append(order)
    return orders


def update_price_tianqin(
        orders: list[COrder],
        account: CAccountTianqin,
        instru_mgr: CInstruMgr,
        drift: float,
):
    tq_contracts = [f"{order.Exchange}.{order.Instrument}" for order in orders]
    last_prices = req_md_last_price_tianqin(
        tq_contracts=tq_contracts,
        tq_account=account.account,
        tq_password=account.password,
    )
    for order in orders:
        contract = f"{order.Exchange}.{order.Instrument}"
        mini_spread = instru_mgr.get_mini_spread(order.Product)
        order.update_order_price(
            price_bounds=last_prices[contract],
            drift=drift,
            mini_spread=mini_spread,
        )
    return 0


def convert_to_integer_multiple(raw: float, minispread: float) -> float:
    return int(np.round(raw // minispread * minispread))


def update_price_wind(
        orders: list[COrder],
        instru_mgr: CInstruMgr,
        drift: float,
        trade_date: str,
):
    exchange_mapper = {
        "SHFE": "SHF",
        "DCE": "DCE",
        "CZCE": "CZC",
        "INE": "INE",
        "GFE": "GFE",
    }
    wd_contracts = [f"{order.Instrument.upper()}.{exchange_mapper[order.Exchange]}" for order in orders]
    md = req_md_trade_date_wind(
        wd_contracts=wd_contracts,
        trade_date=trade_date,
        fields=["settle", "changelt"],
    )
    for order, settle, changelt in zip(orders, md["SETTLE"], md["CHANGELT"]):
        mini_spread = instru_mgr.get_mini_spread(order.Product)
        # if order.Instrument == "AP505":
        #     breakpoint()
        price_bounds = CPriceBounds(
            last=settle,
            upper_lim=convert_to_integer_multiple(settle * (1 + changelt / 100), mini_spread) - mini_spread,
            lower_lim=convert_to_integer_multiple(settle * (1 - changelt / 100), mini_spread) + mini_spread,
        )
        order.update_order_price(
            price_bounds=price_bounds,
            drift=drift,
            mini_spread=mini_spread,
        )
    return 0


def save_orders(
        orders: list[COrder],
        sig_date: str,
        exe_date: str,
        sec_type: str,
        am_or_pm: Literal["am", "pm"],
        orders_file_name_tmpl: str,
        orders_dir: str,
):
    pd.set_option("display.unicode.east_asian_width", True)
    orders_data: list[dict] = [asdict(order) for order in orders]
    if orders_data:
        df = pd.DataFrame(data=orders_data)
        # print(df)
    else:
        df = pd.DataFrame(columns=COrder.names())
        print(f"[INF] There are no orders available for {SFY(sig_date)}-{SFY(sec_type)}-{SFY(am_or_pm)}")
    check_and_makedirs(d := os.path.join(orders_dir, sig_date[0:4], sig_date[4:6]))
    if sec_type == "opn" and am_or_pm == "pm":
        exe_date = sig_date
    orders_file = orders_file_name_tmpl.format(sig_date, exe_date, sec_type, am_or_pm)
    orders_path = os.path.join(d, orders_file)
    df.to_excel(orders_path, index=False, float_format="%.2f", engine='openpyxl')
    print(f"[INF] Orders of {sig_date}-{sec_type}-{am_or_pm} are saved to {SFG(orders_path)}")
    return 0
