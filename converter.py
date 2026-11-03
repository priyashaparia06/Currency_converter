import requests

API_BASE_URL = "https://api.frankfurter.dev/v1"


def get_supported_currencies() -> dict:
    response = requests.get(f"{API_BASE_URL}/currencies", timeout=10)
    response.raise_for_status()
    return response.json()


def convert_currency(from_curr: str, to_curr: str, amount: float) -> float | None:
    if from_curr == to_curr:
        return amount
    response = requests.get(
        f"{API_BASE_URL}/latest",
        params={"base": from_curr, "symbols": to_curr},
        timeout=10,
    )
    response.raise_for_status()
    rate = response.json().get("rates", {}).get(to_curr)
    return amount * rate if rate is not None else None