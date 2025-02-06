import pandas as pd
from husfort.qcalendar import CCalendar


def gen_allocated_equity_from_cash_flow(
        bgn_date: str,
        stp_date: str,
        cash_flow_path: str,
        allocated_equity_path: str,
        calendar: CCalendar,
):
    cash_flow = pd.read_csv(cash_flow_path, dtype={"trade_date": str})
    trade_dates = calendar.get_iter_list(bgn_date, stp_date)
    allocated_equity = pd.DataFrame({"trade_date": trade_dates}).merge(
        right=cash_flow,
        on="trade_date",
        how="left",
    ).fillna(0)
    allocated_equity["equity"] = allocated_equity["cash_flow"].cumsum()
    allocated_equity.to_csv(allocated_equity_path, index=False, float_format="%.2f")
    return 0


class CReaderAllocatedEquity:
    def __init__(self, allocated_equity_path: str):
        self.allocated_equity = pd.read_csv(allocated_equity_path, dtype={"trade_date": str}).set_index("trade_date")

    def get_allocated_equity(self, trade_date: str) -> float:
        return self.allocated_equity.loc[trade_date, "equity"]
