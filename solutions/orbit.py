import os
import httpx
import random
import string
import hashlib
from datetime import datetime
from loguru import logger
from husfort.qlog import define_logger
from typedef import CAccountOrbit
from solutions.orders import parse_tm_from_sec_and_apm

define_logger()


# # httpx 配置
# ACCESS_TOKEN = None


class OrbitException(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f"{self.__class__.__name__}: {super().__str__()} (Code: {self.code})"


class CClient:
    def __init__(self, account_orbit: CAccountOrbit):
        self.__account_orbit = account_orbit
        self.ACCESS_TOKEN = None
        self.__client = httpx.Client(
            event_hooks={"request": [self.before_request],
                         "response": [self.after_response]},
            base_url=account_orbit.server_base_url,
        )

    def before_request(self, request: httpx.Request):
        logger.info(f"Sending reqeust: {request.url}")
        request.headers["User-Agent"] = "Orbit-Python-Examples"
        if self.ACCESS_TOKEN is not None:
            request.headers["Access-Token"] = self.ACCESS_TOKEN

    @staticmethod
    def after_response(response: httpx.Response):
        logger.info(f"Received response status: {response.status_code}")
        if response.is_error:
            response.raise_for_status()
        response.read()
        json = response.json()
        logger.info(f"Received response: {json}")
        if json["code"] < 0:
            raise OrbitException(json.message, json.code)

    def login_by_code(self):
        emp_no = str(self.__account_orbit.emp_no)
        secret = str(self.__account_orbit.api_password)
        nonce = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
        timestamp = str(int(datetime.now().timestamp()))
        params = [emp_no, timestamp, nonce, secret]
        hash_object = hashlib.sha1()
        hash_object.update("".join(sorted(params)).encode("utf-8"))
        signature = hash_object.hexdigest()
        api_code = "_".join([emp_no, timestamp, nonce, signature])
        response = self.__client.post("/auth/loginByCode", json={"code": api_code})
        self.ACCESS_TOKEN = response.json()["data"]["token"]
        return 0

    def query_list(
            self,
            page_no: int = 1,
            page_size: int = 10,
            start_date: str = "2025-01-01",
            end_date: str = "2025-01-01",
    ):
        json = {
            "pageNo": page_no,
            "pageSize": page_size,
            "startDate": start_date,
            "endDate": end_date,
        }
        response = self.__client.post("/quant/queryList", json=json)
        return response.json()["data"]

    def upload(self, json):
        response = self.__client.post("/quant/upload", files={"file": json})
        return response.json()["data"]

    def submit_order(self, rsp):
        json = {"id": rsp["id"]}
        response = self.__client.post("/quant/submitOrder", json=json)
        return response.json()["data"]

    def schedule_order(self, rsp, schedule_time: str):
        json = {"id": rsp["id"], "scheduleTime": schedule_time}
        response = self.__client.post("/quant/scheduleOrder", json=json)
        return response.json()["data"]

    def upload_orders(self, src_path: str = "quant_example.xls", dst_path: str = "quant_example.xls"):
        with open(src_path, "rb") as f:
            j = (dst_path, f, "application/vnd.ms-excel")
            rsp = self.upload(j)
            return rsp


def send_orders_by_orbit(
        account_orbit: CAccountOrbit,
        sig_date: str,
        exe_date: str,
        sec_type: str,
        orders_file_name_tmpl: str,
        orders_dir: str,
):
    client = CClient(account_orbit)
    client.login_by_code()
    client.query_list(page_no=1, page_size=10, start_date="2025-03-06", end_date="2025-03-06")
    d = os.path.join(orders_dir, sig_date[0:4], sig_date[4:6])
    if sec_type == "opn":
        tm_pm = parse_tm_from_sec_and_apm(sec_type, am_or_pm="pm")
        tm_am = parse_tm_from_sec_and_apm(sec_type, am_or_pm="am")
        file_pm = orders_file_name_tmpl.format(sig_date, sig_date, sec_type, "pm", tm_pm)
        file_am = orders_file_name_tmpl.format(sig_date, exe_date, sec_type, "am", tm_am)
        path_pm = os.path.join(d, file_pm)
        path_am = os.path.join(d, file_am)
        schedule_time_pm = f"{sig_date[0:4]}-{sig_date[4:6]}-{sig_date[6:8]} 21:00:00"
        schedule_time_am = f"{exe_date[0:4]}-{exe_date[4:6]}-{exe_date[6:8]} 09:00:00"
        rsp = client.upload_orders(src_path=path_pm, dst_path=file_pm)
        client.schedule_order(rsp, schedule_time=schedule_time_pm)
        rsp = client.upload_orders(src_path=path_am, dst_path=file_am)
        client.schedule_order(rsp, schedule_time=schedule_time_am)
    elif sec_type == "cls":
        tm = parse_tm_from_sec_and_apm(sec_type, am_or_pm="pm")
        file_pm = orders_file_name_tmpl.format(sig_date, exe_date, sec_type, "pm", tm)
        path_pm = os.path.join(d, file_pm)
        schedule_time_pm = f"{exe_date[0:4]}-{exe_date[4:6]}-{exe_date[6:8]} 14:59:00"
        rsp = client.upload_orders(src_path=path_pm, dst_path=file_pm)
        client.schedule_order(rsp, schedule_time=schedule_time_pm)
    else:
        raise ValueError(f"Invalid sig_type: {sec_type}")
    return 0
