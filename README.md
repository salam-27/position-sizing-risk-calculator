# Crypto Futures Position-Size & Risk Calculator (Python + Excel)
🚀 **Live Web App:** [Launch the Calculator on Streamlit](https://position-sizing-risk-calculator.streamlit.app/)
## Project Overview
A fixed-risk position-sizing tool for Crypto Perpetual Futures, built as a **Streamlit web app** with a matching **Excel** version. Instead of guessing a position size, you enter your Entry, Stop Loss and the dollar amount you are willing to lose. The tool returns the exact **Order Value (USDT)** and **Order Qty (Coins)** so that a Stop Loss hit costs you the predefined risk, no more.

It is built as a final pre-trade check: analysis is already done, this confirms your numbers before you place the order on your exchange (Bybit, Bitget, or any other).

## Core Formula
1. **Order Qty (Coins):** `Risk ($) / |Entry Price - Stop Loss|`
2. **Order Value (USDT):** `Order Qty × Entry Price`
3. **Direction:** detected automatically (Stop Loss below Entry = Long, above = Short)

Leverage does **not** change the order size or the dollar risk. It only changes the margin the exchange locks (`Order Value / Leverage`) and how close your liquidation price sits to your entry.

### Example
* **Entry:** `0.87718`
* **Stop Loss:** `0.87678` (stop distance = `0.00040`)
* **Risk:** `$100.00`
* **Order Qty:** `250,000 coins`
* **Order Value:** `$219,295 USDT`

## Features
* **Copy-ready outputs:** Order Value (USDT) and Order Qty (Coins) are shown in copy boxes, formatted to paste straight into the exchange order panel.
* **Always rounds down:** quantity is rounded down to the exchange's step size, so you never risk more than you set.
* **Optional coin selector:** choose from the top 300 USDT perpetuals (live price, quantity step, minimum order size and max leverage loaded from Bitget's public API), or type any coin's prices manually.
* **Leverage & liquidation check (optional):** shows margin required, an estimated liquidation price (Isolated or Cross), and warns when liquidation would hit *before* your Stop Loss.
* **Take Profit & expected return (optional):** enter your own target to see estimated profit, Risk:Reward and return on margin.

## Files in This Repository
* `app.py` — Streamlit position-size calculator.
* `requirements.txt` — Python dependencies (`streamlit`, `requests`).
* `Position size calc.xlsx` — Excel version for quick pre-trade sizing.

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes & Limitations
* Liquidation price is an **estimate**. Real figures depend on the exchange's margin tiers, fees and funding. Always compare with the liquidation price shown on the exchange's order panel.
* Profit and loss figures are before fees, funding and slippage, so real loss at the Stop Loss can be slightly higher.
* The coin list and live prices come from Bitget. Prices on other exchanges can differ slightly, so always enter your actual entry price.
* This tool is for position sizing and risk management only. It is not financial advice.

*Built by Salam Afeez*
