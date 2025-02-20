from tqsdk import TqApi, TqAuth
from typedef import CPriceBounds
from husfort.qutility import SFR
from WindPy import w as wapi
import pandas as pd


def req_md_trade_date_wind(
        wd_contracts: list[str],
        trade_date: str,
        fields: list[str],
) -> dict[str, dict[str, str | float | int | None]]:
    """

    :param wd_contracts: ["RB2505.SHF", "M2505.DCE", "CF505.CZC"]
    :param trade_date:
    :param fields:  ["settle", "changelt"]
    :return:
    """
    wapi.start()
    data = wapi.wss(wd_contracts, fields, options=f"tradeDate={trade_date};cycle=D")
    if data.ErrorCode == 0:
        reqed_data = pd.DataFrame(data.Data, index=fields, columns=data.Codes).T
        return reqed_data.to_dict(orient="index")
    else:
        raise Exception(f"Wind data ErrorCode = {data.ErrorCode}")


def req_md_last_price_tianqin(
        tq_contracts: list[str],
        tq_account: str,
        tq_password: str,
) -> dict[str, CPriceBounds]:
    """

    :param tq_contracts: format = f"{exchange_id}.{contract}", like
                      ["DCE.a2505", "SHFE.rb2505", "CZCE.CF505"]
    :param tq_account:
    :param tq_password:
    :return:
    """
    api = TqApi(auth=TqAuth(user_name=tq_account, password=tq_password))
    quotes = [api.get_quote(contract) for contract in tq_contracts]
    res: dict[str, CPriceBounds | None] = {contract: None for contract in tq_contracts}

    print(f"[INF] {SFR('本函数将请求实时行情,非交易时间调用本函数会导致程序暂停,直到再次收到行情推送.')}")

    while True:
        api.wait_update()
        updated_ids = set()
        for quote in quotes:
            if (quote.last_price is not None) and (quote.upper_limit is not None) and (quote.lower_limit is not None):
                res[quote.instrument_id] = CPriceBounds(
                    last=quote.last_price,
                    upper_lim=quote.upper_limit,
                    lower_lim=quote.lower_limit,
                )
                updated_ids.add(quote.instrument_id)
        if len(updated_ids) == len(tq_contracts):
            break
    api.close()
    return res
