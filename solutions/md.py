from typing import Literal
from tqsdk import TqApi, TqAuth
from dataclasses import asdict, dataclass
from typedef import CPriceBounds


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


if __name__ == "__main__":
    import argparse
    import pandas as pd

    arg_parser = argparse.ArgumentParser("Test of requesting md")
    arg_parser.add_argument("--account", required=True, type=str, help="TQ Account name")
    arg_parser.add_argument("--password", required=True, type=str, help="TQ Account password")
    args = arg_parser.parse_args()

    prices = req_md_last_price_tianqin(
        tq_contracts=["DCE.a2505", "SHFE.rb2505", "CZCE.CF505"],
        tq_account=args.account,
        tq_password=args.password,
    )
    print(pd.DataFrame.from_dict({k: asdict(v) for k, v in prices.items()}, orient="index"))
