import requests
import re
from datetime import date
from sqlalchemy import event
from .models import Product

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"\s+", " ", s)      # collapse multiple spaces
    return s.casefold()             # Unicode-aware lowercasing

@event.listens_for(Product, "before_insert")
def product_before_insert(mapper, connection, target):
    target.name_search = normalize_text(target.name)

@event.listens_for(Product, "before_update")
def product_before_update(mapper, connection, target):
    target.name_search = normalize_text(target.name)

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

    rate = float(data[0]["rate"])
    print(f"Added rate [Date : {d} | Rate : {rate}]")
    return rate