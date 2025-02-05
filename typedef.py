import os
from dataclasses import dataclass
from typing import Literal

CONST_DLNG = 1
CONST_DSRT = -1


@dataclass(frozen=True, eq=True)
class CKey:
    contract: str
    direction: int  # CONST_DLNG or 1 for long, CONST_DSRT or -1 for short


@dataclass
class CTrade:
    key: CKey
    offset: Literal["O", "C"]
    qty: int

    @property
    def op_direction(self) -> Literal["买", "卖"]:
        if self.key.direction == CONST_DLNG:
            return "买" if self.offset == "O" else "卖"
        elif self.key.direction == CONST_DSRT:
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


@dataclass
class CCfg:
    calendar_path: str
    project_data_dir: str
    signals_file_name_tmpl: str
    positions_file_name_tmpl: str

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
