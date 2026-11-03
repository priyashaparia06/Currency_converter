from unittest.mock import patch, MagicMock
import requests
from converter import convert_currency
from server import app


def fake_response(json_data):
    m = MagicMock()
    m.json.return_value = json_data
    m.raise_for_status.return_value = None
    return m


@patch("converter.requests.get")
def test_convert_uses_rate(mock_get):
    mock_get.return_value = fake_response({"rates": {"INR": 83.0}})
    assert convert_currency("USD", "INR", 10) == 830.0


def test_same_currency_no_api_call():
    assert convert_currency("USD", "USD", 25) == 25


@patch("converter.requests.get")
def test_missing_rate_returns_none(mock_get):
    mock_get.return_value = fake_response({"rates": {}})
    assert convert_currency("USD", "XXX", 10) is None


@patch("server.convert_currency", return_value=92.0)
def test_api_convert_ok(_):
    r = app.test_client().get("/convert?amount=100&from=usd&to=eur")
    assert r.status_code == 200
    assert r.get_json()["result"] == 92.0
    assert r.get_json()["from_currency"] == "USD"


def test_api_rejects_bad_amount():
    assert app.test_client().get("/convert?amount=abc&from=USD&to=EUR").status_code == 400


def test_api_rejects_negative_amount():
    assert app.test_client().get("/convert?amount=-5&from=USD&to=EUR").status_code == 400


@patch("server.convert_currency", side_effect=requests.ConnectionError())
def test_api_upstream_down(_):
    assert app.test_client().get("/convert?amount=5&from=USD&to=EUR").status_code == 502


def test_health():
    assert app.test_client().get("/health").get_json() == {"status": "ok"}