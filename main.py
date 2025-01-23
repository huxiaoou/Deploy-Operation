import argparse


def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-d", "--date", required=True, type=str, help="format = 'YYYYMMDD'")
    __args = arg_parser.parse_args()
    return __args


if __name__ == "__main__":
    from solutions.instruments import CInstruMgr

    args = parse_args()
    instru_mgr = CInstruMgr("instruments.yaml")
    instru_mgr.display()

    instru = "AP"
    if instru_mgr.has_ngt(instru):
        print(f"{instru} has night section")
    else:
        print(f"{instru} doesnt have night section")
