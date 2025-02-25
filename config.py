from typedef import CCfg, CHost, CAccountTianqin, CAccountMail

cfg = CCfg(
    calendar_path=r"E:\OneDrive\Data\Calendar\cne_calendar.csv",
    instru_info_path=r"E:\OneDrive\Data\tushare\instruments.csv",
    host=CHost(
        hostname="localhost",
        username="root",
        port=64745,
    ),
    src_signals_dir=r"/root/ProjectsData/Deploy-Alpha/signals",
    project_data_dir=r"E:\Data\Projects\Deploy-Operation",
    signals_file_name_tmpl="signals_sig-date_{}_{}.csv",
    positions_file_name_tqdb_tmpl="positions_sig-date_{}_{}.csv",
    positions_file_name_fuai_tmpl="持仓汇总-{}.xls",
    trades_file_name_tmpl="trades_sig-date_{}_{}.csv",
    orders_file_name_tmpl="orders_sig-date_{}_exe-date_{}_{}_{}.xls",
    drift=0.03,
    account_tianqin=CAccountTianqin(
        userId="15905194497",
        password="Pkusms100871",
    ),
    account_mail=CAccountMail(
        host="smtp.163.com",
        port=25,
        sender="sxzqtest@163.com",
        password="XKdwhjgKeHRim3mb",
    ),
    receivers=["zylxka@126.com"],
    # receivers=["sxzqtest@163.com"],
)
