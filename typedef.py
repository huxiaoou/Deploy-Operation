import os
from enum import Enum
from dataclasses import dataclass, fields
from typing import Literal
from husfort.qremote import CHost
from husfort.qviewer_pnl import CAccountTianqin


class EnumSigs(Enum):
    opn: str = "opn"
    cls: str = "cls"


class EnumPOSD(Enum):
    LNG = 1
    SRT = -1


class EnumOFFSET(Enum):
    OPN = 1
    CLS = -1


class EnumStrategyName(Enum):
    opn: str = "胡晓欧截面CTA开盘"
    cls: str = "胡晓欧截面CTA收盘"

    # opn: str = "胡晓欧截面CTA"
    # cls: str = "胡晓欧截面CTA"


@dataclass(frozen=True, eq=True)
class CKey:
    contract: str
    direction: EnumPOSD


@dataclass
class CTrade:
    key: CKey
    offset: EnumOFFSET
    qty: int
    base_price: float = None
    order_price: float = None

    @property
    def op_direction(self) -> Literal["买", "卖"]:
        if self.key.direction == EnumPOSD.LNG:
            return "买" if self.offset == EnumOFFSET.OPN else "卖"
        elif self.key.direction == EnumPOSD.SRT:
            return "卖" if self.offset == EnumOFFSET.OPN else "买"
        else:
            raise ValueError(f"Invalid direction: {self.key.direction}")

    @property
    def offsetFlag(self) -> Literal["开仓", "平仓"]:
        if self.offset == EnumOFFSET.OPN:
            return "开仓"
        elif self.offset == EnumOFFSET.CLS:
            return "平仓"
        else:
            raise ValueError(f"Invalid offset: {self.offset}")

    def to_dict(self) -> dict:
        return {
            "contract": self.key.contract,
            "direction": self.key.direction.value,
            "qty": self.qty,
            "offset": self.offset.value,
            "base_price": self.base_price,
            "order_price": self.order_price,
        }

    @staticmethod
    def names() -> list[str]:
        return ["contract", "direction", "qty", "offset", "base_price", "order_price"]

    def update_order_price(self, drift: float, mini_spread: float):
        if self.op_direction == "买":
            order_price = self.base_price * (1 + drift)
        else:
            order_price = self.base_price * (1 - drift)
        self.order_price = (order_price // mini_spread) * mini_spread
        return 0


@dataclass
class CPos:
    key: CKey
    qty: int
    base_price: float = None

    def cal_trade_from_another(self, another: "CPos") -> CTrade:
        if (d := self.qty - another.qty) >= 0:
            return CTrade(key=self.key, qty=d, offset=EnumOFFSET.OPN, base_price=self.base_price)
        else:
            return CTrade(key=self.key, qty=-d, offset=EnumOFFSET.CLS, base_price=self.base_price)

    def update_from_trade(self, trade: "CTrade"):
        if trade.offset == EnumOFFSET.OPN:
            self.qty += trade.qty
        else:
            if self.qty < trade.qty:
                raise ValueError(f"self.qty = {self.qty} is lesser than trade.qty = {trade.qty}")
            else:
                self.qty -= trade.qty

    def to_dict(self) -> dict:
        return {
            "contract": self.key.contract,
            "direction": self.key.direction.value,
            "qty": self.qty,
        }


@dataclass(frozen=True)
class CPriceBounds:
    last: float
    upper_lim: float
    lower_lim: float


@dataclass(frozen=True)
class CDepthMd:
    last: float
    open: float
    high: float
    low: float
    pre_close: float
    pre_settle: float
    volume: float
    amount: float
    open_interest: float
    bid_price: float
    ask_price: float
    bid_volume: float
    ask_volume: float
    upper_lim: float
    lower_lim: float


@dataclass
class COrder:
    OrderType: str = "普通单"
    Exchange: str = None  # "DCE", "SHFE", "CZCE"
    Product: str = None  # instrument like "PK"
    Instrument: str = None  # contract like "PK205"
    Direction: Literal["买", "卖"] = None
    OfstFlag: Literal["开仓", "平仓"] = None
    HedgeFlag: str = "投机"
    Price: float = None
    VolumeTotal: int = None
    VolumeTrade: int = None
    Account: str = "CTP模拟"
    Fund: str = "cs3"
    Strategy: str = None  # ["胡晓欧截面CTA收盘", ""胡晓欧截面CTA开盘"]
    Trader: str = "01trader"
    CondOrderInsertPriceType: str = None
    CondCmpPriceType: str = None
    CondRelation1: str = None
    CondPrice1: str = None
    CondRelation2: str = None
    CondPrice2: str = None
    StopLossPrice: str = None
    CancleTime: str = None
    OrderID: str = None

    @staticmethod
    def names() -> list[str]:
        all_fields = fields(COrder)
        return [f.name for f in all_fields]

    @property
    def wind_code(self) -> str:
        exchange_mapper = {
            "SHFE": "SHF",
            "DCE": "DCE",
            "CZCE": "CZC",
            "INE": "INE",
            "GFE": "GFE",
        }
        return f"{self.Instrument.upper()}.{exchange_mapper[self.Exchange]}"

    def update_order_price(self, price_bounds: CPriceBounds, drift: float, mini_spread: float):
        if self.Direction == "买":
            order_price = price_bounds.last * (1 + drift)
            integer_multiple = (order_price // mini_spread) * mini_spread
            self.Price = min(integer_multiple, price_bounds.upper_lim)
        else:
            order_price = price_bounds.last * (1 - drift)
            integer_multiple = (order_price // mini_spread) * mini_spread
            self.Price = max(integer_multiple, price_bounds.lower_lim)
        return 0


@dataclass(frozen=True)
class CAccountMail:
    host: str
    port: int
    sender: str
    password: str


@dataclass(frozen=True)
class CAccountOrbit:
    emp_no: str
    api_password: str
    server_base_url: str


@dataclass
class CCfg:
    calendar_path: str
    instru_info_path: str
    host: CHost
    src_signals_dir: str
    project_data_dir: str
    signals_file_name_tmpl: str
    positions_file_name_tqdb_tmpl: str
    positions_file_name_fuai_tmpl: str
    trades_file_name_tmpl: str
    orders_file_name_tmpl: str
    account_tianqin: CAccountTianqin
    account_mail: CAccountMail
    account_orbit: CAccountOrbit
    receivers: list[str]

    drift: float

    @property
    def cash_flow_path(self) -> str:
        return os.path.join(self.project_data_dir, "cash_flow.csv")

    @property
    def allocated_equity_path(self) -> str:
        return os.path.join(self.project_data_dir, "allocated_equity.csv")

    @property
    def signals_dir(self) -> str:
        return os.path.join(self.project_data_dir, "signals")

    @property
    def positions_dir(self) -> str:
        return os.path.join(self.project_data_dir, "positions")

    @property
    def trades_dir(self) -> str:
        return os.path.join(self.project_data_dir, "trades")

    @property
    def orders_dir(self) -> str:
        return os.path.join(self.project_data_dir, "orders")
