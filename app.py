import threading
import tkinter as tk
from tkinter import messagebox, ttk
import requests

API_BASE_URL = "https://api.frankfurter.dev/v1"


class CurrencyConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Currency Converter")
        self.geometry("420x460")
        self.resizable(False, False)
        self.eval("tk::PlaceWindow . center")

        # Set clean modern style
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.configure(bg="#F3F4F6")

        self.currencies = {}

        self._build_ui()
        self._load_currencies_threaded()

    def _build_ui(self):
        container = tk.Frame(self, bg="#FFFFFF", padx=24, pady=24, bd=1, relief="solid")
        container.pack(padx=20, pady=20, fill="both", expand=True)

        # Header Title
        title_label = tk.Label(
            container,
            text="Currency Converter",
            font=("Helvetica", 16, "bold"),
            bg="#FFFFFF",
            fg="#111827",
        )
        title_label.pack(pady=(0, 16))

        # Amount Entry
        tk.Label(container, text="Amount:", font=("Helvetica", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w")
        self.amount_entry = ttk.Entry(container, font=("Helvetica", 11))
        self.amount_entry.insert(0, "100.00")
        self.amount_entry.pack(fill="x", pady=(4, 12))

        # From Currency Dropdown
        tk.Label(container, text="From Currency:", font=("Helvetica", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w")
        self.from_combo = ttk.Combobox(container, state="readonly", font=("Helvetica", 10))
        self.from_combo.pack(fill="x", pady=(4, 12))

        # Swap Button
        swap_btn = ttk.Button(container, text="⇅ Swap Currencies", command=self._swap_currencies)
        swap_btn.pack(pady=(0, 12))

        # To Currency Dropdown
        tk.Label(container, text="To Currency:", font=("Helvetica", 10, "bold"), bg="#FFFFFF", fg="#374151").pack(anchor="w")
        self.to_combo = ttk.Combobox(container, state="readonly", font=("Helvetica", 10))
        self.to_combo.pack(fill="x", pady=(4, 16))

        # Convert Action Button
        self.convert_btn = tk.Button(
            container,
            text="Convert",
            command=self._on_convert_click,
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            pady=6,
        )
        self.convert_btn.pack(fill="x", pady=(0, 16))

        # Result Displays
        self.result_var = tk.StringVar(value="Select currencies and convert")
        self.result_label = tk.Label(
            container,
            textvariable=self.result_var,
            font=("Helvetica", 13, "bold"),
            bg="#F9FAFB",
            fg="#059669",
            pady=10,
            relief="groove",
        )
        self.result_label.pack(fill="x")

        # Status / Subtitle
        self.status_var = tk.StringVar(value="Fetching supported currencies...")
        self.status_label = tk.Label(
            container,
            textvariable=self.status_var,
            font=("Helvetica", 8),
            bg="#FFFFFF",
            fg="#6B7280",
        )
        self.status_label.pack(side="bottom", pady=(8, 0))

    def _load_currencies_threaded(self):
        """Fetch currencies on a background thread so UI doesn't freeze."""
        threading.Thread(target=self._fetch_currencies_worker, daemon=True).start()

    def _fetch_currencies_worker(self):
        try:
            response = requests.get(f"{API_BASE_URL}/currencies", timeout=10)
            response.raise_for_status()
            self.currencies = response.json()
            options = [f"{code} - {name}" for code, name in sorted(self.currencies.items())]

            self.after(0, self._populate_combos, options)
        except requests.RequestException as e:
            self.after(0, lambda: self.status_var.set("Failed to load currencies."))
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch currency list:\n{e}"))

    def _populate_combos(self, options):
        self.from_combo["values"] = options
        self.to_combo["values"] = options

        # Set default values: USD -> EUR (or fallback to first entries)
        usd_idx = next((i for i, opt in enumerate(options) if opt.startswith("USD")), 0)
        eur_idx = next((i for i, opt in enumerate(options) if opt.startswith("EUR")), min(1, len(options) - 1))

        self.from_combo.current(usd_idx)
        self.to_combo.current(eur_idx)
        self.status_var.set("Ready")

    def _swap_currencies(self):
        from_idx = self.from_combo.current()
        to_idx = self.to_combo.current()
        self.from_combo.current(to_idx)
        self.to_combo.current(from_idx)

    def _on_convert_click(self):
        raw_amount = self.amount_entry.get().strip()
        try:
            amount = float(raw_amount)
            if amount < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid non-negative number for the amount.")
            return

        from_sel = self.from_combo.get()
        to_sel = self.to_combo.get()

        if not from_sel or not to_sel:
            messagebox.showwarning("Missing Currency", "Please select both source and target currencies.")
            return

        from_curr = from_sel.split(" - ")[0]
        to_curr = to_sel.split(" - ")[0]

        self.convert_btn.config(state="disabled", text="Converting...")
        self.status_var.set("Fetching live exchange rate...")

        threading.Thread(
            target=self._convert_worker,
            args=(from_curr, to_curr, amount),
            daemon=True,
        ).start()

    def _convert_worker(self, from_curr, to_curr, amount):
        if from_curr == to_curr:
            self.after(0, self._update_result, amount, to_curr, 1.0)
            return

        try:
            params = {"base": from_curr, "symbols": to_curr}
            response = requests.get(f"{API_BASE_URL}/latest", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            rate = data.get("rates", {}).get(to_curr)

            if rate is not None:
                converted_amount = amount * rate
                self.after(0, self._update_result, converted_amount, to_curr, rate)
            else:
                self.after(0, self._handle_error, "Exchange rate unavailable for this pair.")
        except requests.RequestException as e:
            self.after(0, self._handle_error, f"Network error: {e}")

    def _update_result(self, converted_amount, to_curr, rate):
        self.result_var.set(f"{converted_amount:,.2f} {to_curr}")
        self.status_var.set(f"Rate: 1 = {rate:,.4f} {to_curr}")
        self.convert_btn.config(state="normal", text="Convert")

    def _handle_error(self, message):
        self.status_var.set("Error during conversion")
        self.convert_btn.config(state="normal", text="Convert")
        messagebox.showerror("Conversion Failed", message)


if __name__ == "__main__":
    app = CurrencyConverterApp()
    app.mainloop()