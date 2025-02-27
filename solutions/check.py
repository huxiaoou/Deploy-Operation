import pandas as pd
from typedef import EnumSigs
from solutions.positions import load_position_tqdb, load_position_fuai
from husfort.qutility import SFG, SFY


def check_positions(
        exe_date: str,
        sig_date: str,
        sig_type: EnumSigs,
        positions_file_name_tqdb_tmpl: str,
        positions_file_name_fuai_tmpl: str,
        positions_dir: str,
):
    res_id = f"sig-{sig_date}-exe-{exe_date}-{sig_type.value}"
    act_pos_grp = load_position_fuai(exe_date, sig_type, positions_file_name_fuai_tmpl, positions_dir)
    tgt_pos_grp = load_position_tqdb(sig_date, sig_type, positions_file_name_tqdb_tmpl, positions_dir)
    act_data = pd.DataFrame([v.to_dict() for v in act_pos_grp.values()])
    tgt_data = pd.DataFrame([v.to_dict() for v in tgt_pos_grp.values()])
    merge_data = pd.merge(
        left=tgt_data, right=act_data,
        on=["contract", "direction"],
        how="outer",
        suffixes=("_tgt", "_act"),
    )
    merge_data[["qty_tgt", "qty_act"]] = merge_data[["qty_tgt", "qty_act"]].fillna(0)
    merge_data["diff"] = merge_data["qty_tgt"] - merge_data["qty_act"]
    # print(f"[INF] Target and actual position for {SFG(res_id)}")
    # print(merge_data)
    diff_data = merge_data.query("diff > 0 or diff < 0")
    if diff_data.empty:
        print(f"[INF] {SFG('Congratulations')}, no errors are found for positions of {SFG(res_id)}")
        summary = pd.pivot_table(data=merge_data, index="direction", values="qty_act", aggfunc="sum")
        print(summary)
    else:
        print(f"[WRN] {SFY(res_id)} differences exists.")
        print(diff_data)
    return 0
