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
    sub_arg_parser.add_argument("--sec", type=str, required=True, choices=("opn", "cls"), help="open or close")
    sub_arg_parser.add_argument("--rt", default=False, action="store_true", help="use real time data")
    sub_arg_parser.add_argument("--notsend", default=False, action="store_true", help="not sent emails")

    # --- check
    sub_arg_parser = sub_arg_parsers.add_parser(name="check", help="Check positions")
    sub_arg_parser.add_argument("--sec", type=str, required=True, choices=("opn", "cls"), help="open or close")

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
    import sys
    from husfort.qcalendar import CCalendar
    from husfort.qinstruments import CInstruMgr
    from husfort.qutility import SFY
    from typedef import EnumSigs
    from config import cfg

    calendar = CCalendar(cfg.calendar_path)
    instru_mgr = CInstruMgr(instru_info_path=cfg.instru_info_path)
    args = parse_args()
    sig_date = args.date
    if not calendar.has_date(sig_date):
        print(f"[INF] {SFY(sig_date)} is not a valid trade date")
        sys.exit(0)

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
        from solutions.orders import main_order
        from solutions.emails import send_orders
        from typedef import EnumStrategyName

        exe_date = calendar.get_next_date(sig_date, shift=1)
        sig_type = EnumSigs(args.sec)
        trades = load_trades(
            sig_date=sig_date, sig_type=sig_type,
            trades_file_name_tmpl=cfg.trades_file_name_tmpl, trades_dir=cfg.trades_dir,
        )
        if args.sec == "opn":
            opn_pm_trades, opn_am_trades = split_trades(trades, instru_mgr)
            for tds, am_or_pm in zip([opn_pm_trades, opn_am_trades], ["pm", "am"]):
                main_order(
                    trades=tds, sig_date=sig_date, exe_date=exe_date,
                    sig_type=sig_type, strategy=EnumStrategyName.opn, am_or_pm=am_or_pm,
                    drift=cfg.drift, instru_mgr=instru_mgr,
                    using_rt=args.rt, account_tianqin=cfg.account_tianqin,
                    orders_file_name_tmpl=cfg.orders_file_name_tmpl, orders_dir=cfg.orders_dir,
                )
        elif args.sec == "cls":
            main_order(
                trades=trades, sig_date=sig_date, exe_date=exe_date,
                sig_type=sig_type, strategy=EnumStrategyName.cls, am_or_pm="pm",
                drift=cfg.drift, instru_mgr=instru_mgr,
                using_rt=args.rt, account_tianqin=cfg.account_tianqin,
                orders_file_name_tmpl=cfg.orders_file_name_tmpl, orders_dir=cfg.orders_dir,
            )
        if not args.notsend:
            send_orders(
                account_mail=cfg.account_mail,
                sig_date=sig_date, exe_date=exe_date,
                sec_type=args.sec,
                orders_file_name_tmpl=cfg.orders_file_name_tmpl,
                orders_dir=cfg.orders_dir,
                receivers=cfg.receivers,
            )
    elif args.switch == "check":
        from solutions.check import check_positions

        exe_date = calendar.get_next_date(sig_date, shift=1)
        sig_type = EnumSigs(args.sec)
        check_positions(
            exe_date=exe_date,
            sig_date=sig_date,
            sig_type=sig_type,
            positions_file_name_tqdb_tmpl=cfg.positions_file_name_tqdb_tmpl,
            positions_file_name_fuai_tmpl=cfg.positions_file_name_fuai_tmpl,
            positions_dir=cfg.positions_dir,
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
