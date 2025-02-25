from husfort.qinstruments import CInstruMgr, parse_instrument_from_contract
from husfort.qviewer_pnl import CCfg, CManagerViewer, CPosition, CContract
from solutions.md import req_md_last_price_tianqin
from solutions.positions import load_position_fuai
from typedef import EnumSigs, CAccountTianqin, CKey, CPos, CDepthMd


def convert_pos_to_tq_contracts(poses: dict[CKey, CPos], instru_mgr: CInstruMgr) -> list[str]:
    tq_contracts: list[str] = []
    for key, pos in poses.items():
        instru = parse_instrument_from_contract(contract=key.contract)
        exchange = instru_mgr.get_exchange(instru)
        tq_contract = f"{exchange}.{key.contract}"
        tq_contracts.append(tq_contract)
    return tq_contracts


def convert_pos_to_positions(
        poses: dict[CKey, CPos],
        instru_mgr: CInstruMgr,
        depth_md: dict[str, CDepthMd],
) -> list[CPosition]:
    positions: list[CPosition] = []
    for key, pos in poses.items():
        instru = parse_instrument_from_contract(contract=key.contract)
        exchange = instru_mgr.get_exchange(instru)
        multiplier = instru_mgr.get_multiplier(instru)
        tq_contract = f"{exchange}.{key.contract}"
        base_price = depth_md[tq_contract].pre_close
        position = CPosition(
            contract=CContract(
                contractId=key.contract,
                instrumentId=instru,
                exchangeId=exchange,
                multiplier=multiplier,
            ),
            qty=pos.qty,
            direction=key.direction.value,
            base_price=base_price,
        )
        positions.append(position)
    return positions


def view_pnl(
        exe_date: str,
        sig_type: EnumSigs,
        account: CAccountTianqin,
        positions_file_name_fuai_tmpl: str,
        positions_dir: str,
        instru_mgr: CInstruMgr,
):
    config = CCfg(account=account)
    poses = load_position_fuai(
        sig_date=exe_date,
        sig_type=sig_type,
        positions_file_name_fuai_tmpl=positions_file_name_fuai_tmpl,
        positions_dir=positions_dir,
    )
    tq_contracts = convert_pos_to_tq_contracts(poses, instru_mgr)
    depth_md: dict[str, CDepthMd] = req_md_last_price_tianqin(
        tq_contracts=list(set(tq_contracts)),
        tq_account=account.userId,
        tq_password=account.password,
    )
    positions = convert_pos_to_positions(poses=poses, instru_mgr=instru_mgr, depth_md=depth_md)
    mgr = CManagerViewer(positions=positions, config=config)
    mgr.main()
    return 0
