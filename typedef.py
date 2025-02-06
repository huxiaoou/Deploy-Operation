import os
from dataclasses import dataclass, fields
from typing import Literal

CONST_DLNG = 1
CONST_DSRT = -1
CONST_OFFSET_O = 1
CONST_OFFSET_C = -1


@dataclass(frozen=True, eq=True)
class CKey:
    contract: str
    direction: int  # CONST_DLNG or 1 for long, CONST_DSRT or -1 for short


@dataclass
class CTrade:
    key: CKey
    offset: int  # CONST_OFFSET_O or 1 for open, CONST_OFFSET_C or -1 for close
    qty: int
    base_price: float = None
    order_price: float = None

    @property
    def op_direction(self) -> Literal["买", "卖"]:
        if self.key.direction == CONST_DLNG:
            return "买" if self.offset == CONST_OFFSET_O else "卖"
        elif self.key.direction == CONST_DSRT:
            return "卖" if self.offset == CONST_OFFSET_O else "买"
        else:
            raise ValueError(f"Invalid direction: {self.key.direction}")

    @property
    def offsetFlag(self) -> Literal["开仓", "平仓"]:
        return "开仓" if self.offset == CONST_OFFSET_O else "平仓"

    def to_dict(self) -> dict:
        return {
            "contract": self.key.contract,
            "direction": self.key.direction,
            "qty": self.qty,
            "offset": self.offset,
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
            return CTrade(key=self.key, qty=d, offset=CONST_OFFSET_O, base_price=self.base_price)
        else:
            return CTrade(key=self.key, qty=-d, offset=CONST_OFFSET_C, base_price=self.base_price)

    def update_from_trade(self, trade: "CTrade"):
        if trade.offset == CONST_OFFSET_O:
            self.qty += trade.qty
        else:
            if self.qty < trade.qty:
                raise ValueError(f"self.qty = {self.qty} is lesser than trade.qty = {trade.qty}")
            else:
                self.qty -= trade.qty


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
    Strategy: str = "胡晓欧截面CTA策略"
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


@dataclass
class CCfg:
    calendar_path: str
    instru_info_path: str

    project_data_dir: str
    signals_file_name_tmpl: str
    positions_file_name_tmpl: str
    trades_file_name_tmpl: str
    orders_file_name_tmpl: str

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
