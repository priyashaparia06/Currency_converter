import sys
import requests

API_BASE_URL = "https://api.frankfurter.dev/v1"


def get_supported_currencies() -> dict:
    """Fetch the list of valid currency codes and their full names."""
    try:
        response = requests.get(f"{API_BASE_URL}/currencies", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching supported currencies: {e}")
        return {}


def convert_currency(from_curr: str, to_curr: str, amount: float) -> float | None:
    """Convert an amount from one currency to another using live exchange rates."""
    if from_curr == to_curr:
        return amount

    params = {
        "base": from_curr,
        "symbols": to_curr,
    }

    try:
        response = requests.get(f"{API_BASE_URL}/latest", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        rate = data.get("rates", {}).get(to_curr)
        
        if rate is not None:
            return amount * rate
        return None
    except requests.RequestException as e:
        print(f"Network error during conversion: {e}")
        return None


def main():
    print("=" * 45)
    print("       REAL-TIME CURRENCY CONVERTER          ")
    print("=" * 45)

    print("Fetching active currencies...")
    currencies = get_supported_currencies()
    if not currencies:
        print("Failed to load currency data. Check your network connection.")
        sys.exit(1)

    print(f"Supported currencies: {', '.join(sorted(currencies.keys()))}\n")

    while True:
        # 1. Base Currency
        from_curr = input("From currency (e.g., USD, EUR, INR) or 'q' to quit: ").strip().upper()
        if from_curr == "Q":
            break
        if from_curr not in currencies:
            print(f"Invalid currency code '{from_curr}'. Please choose from the list.\n")
            continue

        # 2. Target Currency
        to_curr = input("To currency (e.g., EUR, GBP, JPY): ").strip().upper()
        if to_curr == "Q":
            break
        if to_curr not in currencies:
            print(f"Invalid currency code '{to_curr}'. Please choose from the list.\n")
            continue

        # 3. Amount to convert
        raw_amount = input(f"Amount in {from_curr}: ").strip()
        try:
            amount = float(raw_amount)
            if amount <= 0:
                print("Amount must be greater than zero.\n")
                continue
        except ValueError:
            print("Invalid input. Please enter a valid numeric value.\n")
            continue

        # 4. Conversion
        result = convert_currency(from_curr, to_curr, amount)
        if result is not None:
            print(f"\n---> {amount:,.2f} {from_curr} ({currencies[from_curr]})")
            print(f"---> {result:,.2f} {to_curr} ({currencies[to_curr]})\n")
        else:
            print("Conversion rate unavailable for this pair.\n")

    print("Thank you for using the Currency Converter!")


if __name__ == "__main__":
    main()