import yaml
from dataclasses import dataclass
from typing import Literal


@dataclass
class CInstrument:
    name: str
    hasNgt: bool
    exchange: Literal["DCE", "SHFE", "CZCE"]


class CInstruMgr:
    def __init__(self, instruments_path: str):
        with open(instruments_path, "r") as f:
            _config = yaml.safe_load(f)
            self.mgr: dict[str, CInstrument] = {
                instru_name: CInstrument(instru_name, **instru_config)
                for instru_name, instru_config in _config.items()
            }

    def display(self):
        for instru in self.mgr.values():
            print(instru)

    def has_ngt(self, instru: str) -> bool:
        return self.mgr[instru].hasNgt

    def get_exchange(self, instru: str) -> Literal["DCE", "SHFE", "CZCE"]:
        return self.mgr[instru].exchange
