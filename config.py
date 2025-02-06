from typedef import CCfg

cfg = CCfg(
    calendar_path=r"E:\OneDrive\Data\Calendar\cne_calendar.csv",
    instru_info_path=r"E:\OneDrive\Data\tushare\instruments.csv",
    project_data_dir=r"E:\Data\Projects\Deploy-Operation",
    signals_file_name_tmpl="signals_sig-date_{}_{}.csv",
    positions_file_name_tmpl="positions_sig-date_{}_{}.csv",
    trades_file_name_tmpl="trades_sig-date_{}_{}.csv",
    orders_file_name_tmpl="orders_sig-date_{}_exe-date_{}_{}.csv",
)
