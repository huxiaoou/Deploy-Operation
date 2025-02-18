import argparse


def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-d", "--date", type=str, required=True, help="date of signals, format=[YYYYMMDD]")

    sub_arg_parsers = arg_parser.add_subparsers(
        title="switch to sub functions",
        dest="switch",
        description="use this position argument to call different functions of this project. "
                    "For example: 'python main.py '",
        required=True,
    )

    # --- allocated equity
    sub_arg_parser = sub_arg_parsers.add_parser(name="allocated", help="Calculate allocated equity from cash flows")
    sub_arg_parser.add_argument(
        "--bgn", type=str, default="20241201", help="begin date, format = [YYYYMMDD]")

    # --- sync signals
    sub_arg_parsers.add_parser(name="sync", help="Sync signals")

    # --- positions
    sub_arg_parsers.add_parser(name="positions", help="Calculate positions from allocated and signals")

    # --- trades
    sub_arg_parser = sub_arg_parsers.add_parser(name="trades", help="Calculate trades from positions")
    sub_arg_parser.add_argument("--usetq", default=False, action="store_true",
                                help="Use this flag to use trans-quant data instead of fuai data")

    # --- orders
    sub_arg_parser = sub_arg_parsers.add_parser(name="orders", help="Convert trades to orders")
    sub_arg_parser.add_argument("--sec", type=str, required=True, choices=("opn", "cls"), help="date of signals")
    sub_arg_parser.add_argument("--type", type=str, required=True, choices=("real", "last"), help="type of data source")

    # --- tests
    sub_arg_parser = sub_arg_parsers.add_parser(name="test", help="do some tests")
    sub_arg_parser.add_argument(
        "--sub", type=str, required=True, choices=("tianqin", "wind"), help="'tianqin' or 'wind'",
    )
    sub_arg_parser.add_argument("--account", type=str, default=None, help="TQ Account name")
    sub_arg_parser.add_argument("--password", type=str, default=None, help="TQ Account password")

    __args = arg_parser.parse_args()
    return __args


if __name__ == "__main__":
    from husfort.qcalendar import CCalendar
    from husfort.qinstruments import CInstruMgr
    from typedef import EnumSigs
    from config import cfg

    calendar = CCalendar(cfg.calendar_path)
    instru_mgr = CInstruMgr(instru_info_path=cfg.instru_info_path)
    args = parse_args()
    sig_date = args.date

    if args.switch == "allocated":
        from solutions.allocated_equity import gen_allocated_equity_from_cash_flow

        bgn, end = args.bgn, sig_date
        stp = calendar.get_next_date(end, shift=1)
        gen_allocated_equity_from_cash_flow(
            bgn_date=bgn,
            stp_date=stp,
            cash_flow_path=cfg.cash_flow_path,
            allocated_equity_path=cfg.allocated_equity_path,
            calendar=calendar,
        )
    elif args.switch == "sync":
        from solutions.sync import download_signals_from

        for sig_type in EnumSigs:
            download_signals_from(
                sig_date=sig_date,
                sig_type=sig_type,
                signals_file_name_tmpl=cfg.signals_file_name_tmpl,
                src_signals_dir=cfg.src_signals_dir,
                dst_signals_dir=cfg.signals_dir,
                host=cfg.host,
            )
    elif args.switch == "positions":
        from solutions.allocated_equity import CReaderAllocatedEquity
        from solutions.positions import convert_signal_to_positions

        reader_alloc = CReaderAllocatedEquity(cfg.allocated_equity_path)
        for sig_type in EnumSigs:
            convert_signal_to_positions(
                sig_date=sig_date,
                sig_type=sig_type,
                signals_file_name_tmpl=cfg.signals_file_name_tmpl,
                positions_file_name_tmpl=cfg.positions_file_name_tqdb_tmpl,
                signals_dir=cfg.signals_dir,
                positions_dir=cfg.positions_dir,
                allocated_equity=reader_alloc.get_allocated_equity(sig_date) * 0.5,
                instru_mgr=instru_mgr,
            )
    elif args.switch == "trades":
        from solutions.trades import gen_trades
        from solutions.trades import save_trades

        prev_sig_date = calendar.get_next_date(sig_date, -1)
        for sig_type in EnumSigs:
            trades_opn = gen_trades(
                this_sig_date=sig_date,
                prev_sig_date=prev_sig_date,
                sig_type=sig_type,
                positions_file_name_tqdb_tmpl=cfg.positions_file_name_tqdb_tmpl,
                positions_file_name_fuai_tmpl=cfg.positions_file_name_fuai_tmpl,
                positions_dir=cfg.positions_dir,
                use_tq=args.usetq,
            )
            save_trades(trades_opn, sig_date, sig_type, cfg.trades_file_name_tmpl, cfg.trades_dir)

    elif args.switch == "orders":
        from solutions.trades import load_trades, split_trades
        from solutions.orders import convert_trades_to_orders, update_price_tianqin, update_price_wind, save_orders
        from typedef import EnumStrategyName

        exe_date = calendar.get_next_date(sig_date, shift=1)
        sig_type = EnumSigs(args.sec)
        trades = load_trades(
            sig_date=sig_date, sig_type=sig_type,
            trades_file_name_tmpl=cfg.trades_file_name_tmpl, trades_dir=cfg.trades_dir,
        )
        if args.sec == "opn":
            opn_pm_trades, opn_am_trades = split_trades(trades, instru_mgr)
            opn_pm_orders = convert_trades_to_orders(opn_pm_trades, instru_mgr, cfg.drift, EnumStrategyName.opn.value)
            opn_am_orders = convert_trades_to_orders(opn_am_trades, instru_mgr, cfg.drift, EnumStrategyName.opn.value)
            if args.type == "real":
                update_price_tianqin(opn_pm_orders, cfg.account_tianqin, instru_mgr, cfg.drift)
                update_price_tianqin(opn_am_orders, cfg.account_tianqin, instru_mgr, cfg.drift)
            elif args.type == "last":
                update_price_wind(opn_pm_orders, instru_mgr, cfg.drift, sig_date)
                update_price_wind(opn_am_orders, instru_mgr, cfg.drift, sig_date)
            save_orders(
                orders=opn_pm_orders,
                sig_date=sig_date, exe_date=exe_date,
                sec_type="opn", am_or_pm="pm",
                orders_file_name_tmpl=cfg.orders_file_name_tmpl,
                orders_dir=cfg.orders_dir,
            )
            save_orders(
                orders=opn_am_orders,
                sig_date=sig_date, exe_date=exe_date,
                sec_type="opn", am_or_pm="am",
                orders_file_name_tmpl=cfg.orders_file_name_tmpl,
                orders_dir=cfg.orders_dir,
            )
        elif args.sec == "cls":
            cls_orders = convert_trades_to_orders(trades, instru_mgr, cfg.drift, EnumStrategyName.cls.value)
            if args.type == "real":
                update_price_tianqin(cls_orders, cfg.account_tianqin, instru_mgr, cfg.drift)
            elif args.type == "last":
                update_price_wind(cls_orders, instru_mgr, cfg.drift, sig_date)
            save_orders(
                orders=cls_orders,
                sig_date=sig_date, exe_date=exe_date,
                sec_type="cls", am_or_pm="pm",
                orders_file_name_tmpl=cfg.orders_file_name_tmpl,
                orders_dir=cfg.orders_dir,
            )
    elif args.switch == "test":
        if args.sub == "tianqin":
            import pandas as pd
            from dataclasses import asdict
            from solutions.md import req_md_last_price_tianqin

            prices = req_md_last_price_tianqin(
                tq_contracts=["DCE.a2505", "SHFE.rb2505", "CZCE.CF505"],
                tq_account=args.account,
                tq_password=args.password,
            )
            print(pd.DataFrame.from_dict({k: asdict(v) for k, v in prices.items()}, orient="index"))
        elif args.sub == "wind":
            from solutions.md import req_md_trade_date_wind

            data = req_md_trade_date_wind(
                wd_contracts=["RB2505.SHF", "M2505.DCE", "CF505.CZC"],
                # wd_contracts=["rb2505", "m2505", "CF505"],
                trade_date=sig_date,
                fields=["settle", "changelt"],
            )
            print(data)
        else:
            raise ValueError(f"Invalid argument 'sub': {args.sub}")
    else:
        raise ValueError(f"Invalid switch = {args.switch}")
