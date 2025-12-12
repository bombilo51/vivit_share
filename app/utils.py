import requests
from datetime import date

def get_usd_uah_rate(d: date | None = None) -> float:
    base_url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
    params = {"valcode": "USD", "json": ""}

    if d is not None:
        # NBU expects YYYYMMDD (no dashes)
        params["date"] = d.strftime("%Y%m%d")

    resp = requests.get(base_url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if not data:
        raise ValueError("Empty response from NBU API")

    return float(data[0]["rate"])