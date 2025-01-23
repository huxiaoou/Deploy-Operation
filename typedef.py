from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, eq=True)
class CKey:
    contract: str
    direction: Literal["L", "S"]


@dataclass
class CTrade:
    key: CKey
    offset: Literal["O", "C"]
    qty: int

    @property
    def direction(self) -> Literal["买", "卖"]:
        if self.key.direction == "L":
            return "买" if self.offset == "O" else "卖"
        elif self.key.direction == "S":
            return "卖" if self.offset == "O" else "买"
        else:
            raise ValueError(f"Invalid direction: {self.key.direction}")

    @property
    def offsetFlag(self) -> Literal["开仓", "平仓"]:
        return "开仓" if self.offset == "O" else "平仓"


@dataclass
class CPos:
    key: CKey
    qty: int

    def cal_trade_from_another(self, another: "CPos") -> CTrade:
        if (d := self.qty - another.qty) >= 0:
            return CTrade(key=self.key, qty=d, offset="O")
        else:
            return CTrade(key=self.key, qty=-d, offset="C")

    def update_from_trade(self, trade: "CTrade"):
        if trade.offset == "O":
            self.qty += trade.qty
        else:
            if self.qty < trade.qty:
                raise ValueError(f"self.qty = {self.qty} is lesser than trade.qty = {trade.qty}")
            else:
                self.qty -= trade.qty


@dataclass
class COrder:
    OrderType: str = "普通单"
    Exchange: Literal["DCE", "SHFE", "CZCE"] = None
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
    Strategy: str = "截面CTA策略"
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
