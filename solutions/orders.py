import os
import numpy as np
import pandas as pd
from typing import Literal
from dataclasses import asdict
from husfort.qutility import check_and_makedirs, SFG, SFY
from husfort.qinstruments import CInstruMgr, parse_instrument_from_contract
from typedef import CTrade, COrder, CAccountTianqin, CPriceBounds, EnumSigs, EnumStrategyName, CDepthMd
from solutions.md import req_depth_md_tianqin, req_md_trade_date_wind


def parse_tm_from_sec_and_apm(sec_type: str, am_or_pm: str) -> str:
    if (sec_type, am_or_pm) == ("opn", "pm"):
        return "2100"
    elif (sec_type, am_or_pm) == ("opn", "am"):
        return "0900"
    elif (sec_type, am_or_pm) == ("cls", "pm"):
        return "1459"
    else:
        raise ValueError(f"Invalid combo for {sec_type}, {am_or_pm}")


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


def adjust_for_regulation_exception(orders: list[COrder]):
    def __exception_0(o: COrder):
        if o.Product == "RM":
            if o.OfstFlag == "开仓":
                q = o.VolumeTotal
                o.VolumeTotal = int(np.round(q / 10) * 10)
                print(
                    f"[INF] Quantity of Order {SFG(o.Instrument)}-{SFG(o.Direction)}-{SFG(o.OfstFlag)} is adjusted from {SFY(q)} to {SFG(order.VolumeTotal)}"
                )

    print(f"[INF] Adjust orders for regulation")
    for order in orders:
        __exception_0(order)
    return 0


def update_price_tianqin(
        orders: list[COrder],
        account: CAccountTianqin,
        instru_mgr: CInstruMgr,
        drift: float,
):
    tq_contracts = [f"{order.Exchange}.{order.Instrument}" for order in orders]
    depth_md: dict[str, CDepthMd] = req_depth_md_tianqin(
        tq_contracts=list(set(tq_contracts)),
        tq_account=account.userId,
        tq_password=account.password,
    )
    for order in orders:
        contract = f"{order.Exchange}.{order.Instrument}"
        mini_spread = instru_mgr.get_mini_spread(order.Product)
        cntrct_depth_md = depth_md[contract]
        price_bounds = CPriceBounds(
            last=cntrct_depth_md.last,
            upper_lim=cntrct_depth_md.upper_lim,
            lower_lim=cntrct_depth_md.lower_lim,
        )
        order.update_order_price(
            price_bounds=price_bounds,
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
    wd_contracts = [order.wind_code for order in orders]
    md = req_md_trade_date_wind(
        wd_contracts=list(set(wd_contracts)),
        trade_date=trade_date,
        fields=["settle", "changelt"],
    )
    for order in orders:
        order_req_data = md[order.wind_code]
        settle, changelt = order_req_data["settle"], order_req_data["changelt"]
        mini_spread = instru_mgr.get_mini_spread(order.Product)
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
        # if order.wind_code == "AP505.CZC":
        #     breakpoint()
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
    tm = parse_tm_from_sec_and_apm(sec_type, am_or_pm)
    orders_file = orders_file_name_tmpl.format(sig_date, exe_date, sec_type, am_or_pm, tm)
    orders_path = os.path.join(d, orders_file)
    df.to_excel(orders_path, index=False, float_format="%.2f", engine='openpyxl')
    print(f"[INF] Orders of {sig_date}-{sec_type}-{am_or_pm} are saved to {SFG(orders_path)}")
    return 0


def main_order(
        trades: list[CTrade],
        sig_date: str,
        exe_date: str,
        sig_type: EnumSigs,
        am_or_pm: Literal["am", "pm"],
        strategy: EnumStrategyName,
        drift: float,
        instru_mgr: CInstruMgr,
        using_rt: bool,
        account_tianqin: CAccountTianqin,
        orders_file_name_tmpl: str,
        orders_dir: str,
):
    orders = convert_trades_to_orders(trades, instru_mgr, drift, strategy=strategy.value)
    if using_rt:
        update_price_tianqin(orders, account_tianqin, instru_mgr, drift)
    else:
        update_price_wind(orders, instru_mgr, drift, sig_date)
    adjust_for_regulation_exception(orders)
    save_orders(
        orders=orders,
        sig_date=sig_date, exe_date=exe_date,
        sec_type=sig_type.value,
        am_or_pm=am_or_pm,
        orders_file_name_tmpl=orders_file_name_tmpl,
        orders_dir=orders_dir,
    )
    return 0
