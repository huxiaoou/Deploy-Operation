from typing import Literal
from tqsdk import TqApi, TqAuth
import numpy as np


def req_md_trade_date_wind(
        contracts: list[str],
        trade_date: str,
        price: Literal["open", "close"] = "close",
) -> dict[str, float]:
    raise NotImplementedError


def req_md_last_price_wind(contracts: list[str]) -> dict[str, float]:
    raise NotImplementedError


def req_md_last_price_tianqin(
        tq_contracts: list[str],
        tq_account: str,
        tq_password: str,
) -> dict[str, float]:
    """

    :param tq_contracts: format = f"{exchange_id}.{contract}", like
                      ["DCE.a2505", "SHFE.rb2505", "CZCE.CF505"]
    :param tq_account:
    :param tq_password:
    :return:
    """
    api = TqApi(auth=TqAuth(user_name=tq_account, password=tq_password))
    quotes = [api.get_quote(contract) for contract in tq_contracts]
    res: dict[str, float] = {contract: np.nan for contract in tq_contracts}

    while True:
        api.wait_update()
        updated_ids = set()
        for quote in quotes:
            res[quote.instrument_id] = quote.last_price
            if res[quote.instrument_id] is not None:
                updated_ids.add(quote.instrument_id)
        if len(updated_ids) == len(tq_contracts):
            break
    api.close()
    return res


if __name__ == "__main__":
    import argparse
    import pandas as pd

    arg_parser = argparse.ArgumentParser("Test of requesting md")
    arg_parser.add_argument("--account", required=True, type=str, help="TQ Account name")
    arg_parser.add_argument("--password", required=True, type=str, help="TQ Account password")
    args = arg_parser.parse_args()

    last_price = req_md_last_price_tianqin(
        tq_contracts=["DCE.a2505", "SHFE.rb2505", "CZCE.CF505"],
        tq_account=args.account,
        tq_password=args.password,
    )

    print(pd.DataFrame({"last_price": last_price}))
