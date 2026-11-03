from flask import Flask, jsonify, request
import requests
from converter import get_supported_currencies, convert_currency

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/currencies")
def currencies():
    try:
        return jsonify(get_supported_currencies())
    except requests.RequestException:
        return jsonify(error="Upstream rate service unavailable"), 502


@app.route("/convert")
def convert():
    from_curr = request.args.get("from", "").upper()
    to_curr = request.args.get("to", "").upper()
    try:
        amount = float(request.args.get("amount", ""))
    except ValueError:
        return jsonify(error="amount must be a number"), 400
    if amount <= 0:
        return jsonify(error="amount must be greater than zero"), 400
    if not from_curr or not to_curr:
        return jsonify(error="from and to are required"), 400

    try:
        result = convert_currency(from_curr, to_curr, amount)
    except requests.RequestException:
        return jsonify(error="Upstream rate service unavailable"), 502

    if result is None:
        return jsonify(error="Rate unavailable for this pair"), 404
    return jsonify(amount=amount, from_currency=from_curr,
                   to_currency=to_curr, result=round(result, 2))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)