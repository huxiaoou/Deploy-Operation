import argparse


def parse_args():
    arg_parser = argparse.ArgumentParser()
    sub_arg_parsers = arg_parser.add_subparsers(
        title="switch to sub functions",
        dest="switch",
        description="use this position argument to call different functions of this project. "
                    "For example: 'python main.py '",
        required=True,
    )

    # --- allocated equity
    sub_arg_parser = sub_arg_parsers.add_parser(name="allocated", help="Calculate allocated equity from cash flows")
    sub_arg_parser.add_argument("--bgn", type=str, default="20241201", help="begin date, format = [YYYYMMDD]")
    sub_arg_parser.add_argument("--stp", type=str, default="20300101", help="stop date, format = [YYYYMMDD]")

    # --- sync signals

    # --- positions
    sub_arg_parser = sub_arg_parsers.add_parser(name="positions", help="Calculate positions from allocated and signals")
    sub_arg_parser.add_argument("-d", "--date", type=str, required=True, help="date of signals")

    # --- trades
    sub_arg_parser = sub_arg_parsers.add_parser(name="trades", help="Calculate trades from positions")
    sub_arg_parser.add_argument("-d", "--date", type=str, required=True, help="date of signals")

    # --- orders
    sub_arg_parser = sub_arg_parsers.add_parser(name="orders", help="Convert trades to orders")
    sub_arg_parser.add_argument("-d", "--date", type=str, required=True, help="date of signals")

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

        bgn, stp = args.bgn, args.stp
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
                allocated_equity=reader_alloc.get_allocated_equity(sig_date),
                instru_mgr=instru_mgr,
            )
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
        raise NotImplementedError
    else:
        raise ValueError(f"Invalid switch = {args.switch}")
