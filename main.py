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
    sub_arg_parsers.add_parser(name="trades", help="Calculate trades from positions")

    # --- orders
    sub_arg_parser = sub_arg_parsers.add_parser(name="orders", help="Convert trades to orders")
    sub_arg_parser.add_argument("-s", "--sec", type=str, required=True, choices=("opn", "cls"), help="date of signals")

    __args = arg_parser.parse_args()
    return __args


if __name__ == "__main__":
    from husfort.qcalendar import CCalendar
    from husfort.qinstruments import CInstruMgr
    from config import cfg

    calendar = CCalendar(cfg.calendar_path)
    instru_mgr = CInstruMgr(instru_info_path=cfg.instru_info_path)
    args = parse_args()

    if args.switch == "allocated":
        from solutions.allocated_equity import gen_allocated_equity_from_cash_flow

        bgn, end = args.bgn, args.date
        stp = calendar.get_next_date(end, shift=1)
        gen_allocated_equity_from_cash_flow(
            bgn_date=bgn,
            stp_date=stp,
            cash_flow_path=cfg.cash_flow_path,
            allocated_equity_path=cfg.allocated_equity_path,
            calendar=calendar,
        )
    elif args.switch == "positions":
        from solutions.allocated_equity import CReaderAllocatedEquity
        from solutions.positions import convert_signal_to_positions

        sig_date = args.date
        reader_alloc = CReaderAllocatedEquity(cfg.allocated_equity_path)
        for sig_type in ["opn", "cls"]:
            convert_signal_to_positions(
                sig_date=sig_date,
                sig_type=sig_type,
                signals_file_name_tmpl=cfg.signals_file_name_tmpl,
                positions_file_name_tmpl=cfg.positions_file_name_tmpl,
                signals_dir=cfg.signals_dir,
                positions_dir=cfg.positions_dir,
                allocated_equity=reader_alloc.get_allocated_equity(sig_date) * 0.5,
                instru_mgr=instru_mgr,
            )
    elif args.switch == "sync":
        raise NotImplementedError
    elif args.switch == "trades":
        from solutions.trades import gen_trades
        from solutions.trades import save_trades

        this_sig_date = args.date
        prev_sig_date = calendar.get_next_date(this_sig_date, -1)
        for sig_type in ["opn", "cls"]:
            trades_opn = gen_trades(
                this_sig_date=this_sig_date,
                prev_sig_date=prev_sig_date,
                sig_type=sig_type,
                positions_file_name_tmpl=cfg.positions_file_name_tmpl,
                positions_dir=cfg.positions_dir,
            )
            save_trades(trades_opn, this_sig_date, sig_type, cfg.trades_file_name_tmpl, cfg.trades_dir)

    elif args.switch == "orders":
        from solutions.trades import load_trades, split_trades
        from solutions.orders import convert_trades_to_orders, save_orders

        sig_date = args.date
        exe_date = calendar.get_next_date(sig_date, shift=1)
        trades = load_trades(
            sig_date=sig_date, sec_type=args.sec,
            trades_file_name_tmpl=cfg.trades_file_name_tmpl, trades_dir=cfg.trades_dir,
        )
        if args.sec == "opn":
            opn_pm_trades, opn_am_trades = split_trades(trades, instru_mgr)
            opn_pm_orders = convert_trades_to_orders(opn_pm_trades, instru_mgr, cfg.drift)
            opn_am_orders = convert_trades_to_orders(opn_am_trades, instru_mgr, cfg.drift)
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
            cls_orders = convert_trades_to_orders(trades, instru_mgr, cfg.drift)
            save_orders(
                orders=cls_orders,
                sig_date=sig_date, exe_date=exe_date,
                sec_type="cls", am_or_pm="pm",
                orders_file_name_tmpl=cfg.orders_file_name_tmpl,
                orders_dir=cfg.orders_dir,
            )
    else:
        raise ValueError(f"Invalid switch = {args.switch}")
