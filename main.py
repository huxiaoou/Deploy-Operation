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

    sub_arg_parser = sub_arg_parsers.add_parser(name="allocated", help="Calculate allocated equity from cash flows")
    sub_arg_parser.add_argument("--bgn", type=str, default="20250102", help="begin date, format = [YYYYMMDD]")
    sub_arg_parser.add_argument("--stp", type=str, default="20260101", help="stop date, format = [YYYYMMDD]")

    __args = arg_parser.parse_args()
    return __args


if __name__ == "__main__":
    from config import cfg
    from husfort.qcalendar import CCalendar

    args = parse_args()
    calendar = CCalendar(cfg.calendar_path)

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
