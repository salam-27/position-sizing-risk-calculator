import streamlit as st
import requests
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

st.set_page_config(page_title="Position Size Calculator", page_icon="⚡", layout="centered")

st.title("⚡ Position Size Calculator")
st.caption("Bybit / Bitget USDT Perpetuals • Hedge Mode • Built by Salam Afeez")

# ============ DATA: TOP 200 PERPS ============
@st.cache_data(ttl=60, show_spinner="Loading top 200 pairs…")
def load_pairs(exchange: str):
    """Returns list of dicts: symbol, price, price_dp, qty_step, min_qty, max_lev (sorted by 24h volume)."""
    rows = []
    if exchange == "Bitget":
        base = "https://api.bitget.com/api/v2/mix/market"
        t = requests.get(f"{base}/tickers", params={"productType": "USDT-FUTURES"}, timeout=10).json()["data"]
        c = requests.get(f"{base}/contracts", params={"productType": "USDT-FUTURES"}, timeout=10).json()["data"]
        meta = {x["symbol"]: x for x in c}
        for x in t:
            m = meta.get(x["symbol"])
            if not m or m.get("symbolStatus", "normal") != "normal":
                continue
            step = m.get("sizeMultiplier") or str(Decimal(1).scaleb(-int(m["volumePlace"])))
            rows.append(dict(
                symbol=x["symbol"], price=float(x["lastPr"]),
                vol=float(x.get("usdtVolume") or x.get("quoteVolume") or 0),
                price_dp=int(m["pricePlace"]), qty_step=str(step),
                min_qty=str(m.get("minTradeNum", step)), max_lev=int(float(m.get("maxLever", 50))),
            ))
    else:  # Bybit
        t = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "linear"}, timeout=10).json()["result"]["list"]
        i = requests.get("https://api.bybit.com/v5/market/instruments-info",
                         params={"category": "linear", "limit": 1000}, timeout=10).json()["result"]["list"]
        meta = {x["symbol"]: x for x in i if x.get("quoteCoin") == "USDT" and x.get("status") == "Trading"
                and x.get("contractType") == "LinearPerpetual"}
        for x in t:
            m = meta.get(x["symbol"])
            if not m:
                continue
            tick = Decimal(m["priceFilter"]["tickSize"])
            rows.append(dict(
                symbol=x["symbol"], price=float(x["lastPrice"]), vol=float(x.get("turnover24h", 0)),
                price_dp=max(0, -tick.normalize().as_tuple().exponent),
                qty_step=m["lotSizeFilter"]["qtyStep"], min_qty=m["lotSizeFilter"]["minOrderQty"],
                max_lev=int(float(m["leverageFilter"]["maxLeverage"])),
            ))
    rows.sort(key=lambda r: r["vol"], reverse=True)
    return rows[:200]

# ============ STEP 1: EXCHANGE + PAIR ============
MANUAL = "✏️ Manual (type any coin's prices)"

def on_exchange_change():
    st.session_state.pair = MANUAL

def on_pair_change():
    p = st.session_state.get("pair_lookup", {}).get(st.session_state.pair)
    if p:
        st.session_state.entry = p["price"]
        st.session_state.sl = round(p["price"] * 0.995, p["price_dp"])   # starter SL, change it

if "pair" not in st.session_state:
    st.session_state.pair = MANUAL
    st.session_state.entry = 0.87718
    st.session_state.sl = 0.87678

st.subheader("1. Choose exchange & coin")
ex_col, pair_col = st.columns([1, 2])
with ex_col:
    exchange = st.selectbox("Exchange", ["Bitget", "Bybit"], key="exchange", on_change=on_exchange_change)

pairs, load_error = [], None
try:
    pairs = load_pairs(exchange)
except Exception as e:
    load_error = str(e)

lookup = {p["symbol"]: p for p in pairs}
st.session_state.pair_lookup = lookup
with pair_col:
    st.selectbox("Coin (type to search)", [MANUAL] + list(lookup.keys()), key="pair", on_change=on_pair_change)

if load_error:
    st.warning("Could not load live pairs (the exchange API may be blocked from this server). Manual mode still works.")

pair = lookup.get(st.session_state.pair)
price_dp = pair["price_dp"] if pair else 6
qty_step = Decimal(pair["qty_step"]) if pair else Decimal("1")
min_qty = Decimal(pair["min_qty"]) if pair else Decimal("0")
max_lev = pair["max_lev"] if pair else 125

if pair:
    st.caption(f"Live price **{pair['price']}** • Qty step **{pair['qty_step']}** • Min qty **{pair['min_qty']}** • Max leverage **{pair['max_lev']}x**")
    if st.button("🔄 Use latest price as Entry"):
        load_pairs.clear()
        fresh = {p["symbol"]: p for p in load_pairs(exchange)}.get(st.session_state.pair)
        if fresh:
            st.session_state.entry = fresh["price"]
            st.rerun()
else:
    qty_step = Decimal(str(st.selectbox("Qty step (manual mode)", [1, 0.1, 0.01, 0.001, 0.0001], index=0)))

# ============ STEP 2: TRADE INPUTS ============
st.subheader("2. Enter your trade")
tick = 10 ** (-price_dp)
c1, c2, c3 = st.columns(3)
with c1:
    entry_price = st.number_input("Entry Price", min_value=0.0, step=tick, format=f"%.{price_dp}f", key="entry")
with c2:
    stop_loss = st.number_input("Stop Loss", min_value=0.0, step=tick, format=f"%.{price_dp}f", key="sl")
with c3:
    risk_dollars = st.number_input("Risk (USDT)", min_value=0.1, value=100.0, step=1.0, format="%.2f")

# ============ STEP 3: LEVERAGE & MARGIN ============
st.subheader("3. Leverage & margin mode")
l1, l2 = st.columns(2)
with l1:
    leverage = st.number_input(f"Leverage (x) — max {max_lev}x", min_value=1, max_value=max_lev, value=min(20, max_lev), step=1)
with l2:
    mode = st.radio("Margin mode", ["Isolated", "Cross"], horizontal=True)

l3, l4 = st.columns(2)
with l3:
    balance = st.number_input("Futures account balance (USDT)", min_value=0.0, value=1000.0, step=50.0,
                              help="Used for the margin check, and for liquidation in Cross mode.")
with l4:
    mmr_pct = st.number_input("Maintenance margin rate (%)", min_value=0.0, max_value=5.0, value=0.5, step=0.1,
                              help="Approximate. Real rate depends on position size tier. Check the exchange.")

st.info(
    "**Isolated** = only the margin you give this trade can be lost; liquidation is predictable. "
    "**Cross** = the exchange can use your whole futures balance to keep the trade open, so liquidation is further away "
    "but a loss can be far bigger than the trade's own margin. "
    "Neither mode changes your order size or your risk at Stop Loss. Both change *when you get liquidated*."
)

# ============ CALCULATION ============
E, SL, R = Decimal(str(entry_price)), Decimal(str(stop_loss)), Decimal(str(risk_dollars))
distance = abs(E - SL)
st.divider()

if E <= 0 or SL <= 0:
    st.error("⚠️ Enter a valid Entry and Stop Loss.")
    st.stop()
if distance == 0:
    st.error("⚠️ Entry Price and Stop Loss cannot be the same.")
    st.stop()

is_long = E > SL
qty = ((R / distance) // qty_step) * qty_step          # always rounded DOWN
if qty < min_qty or qty <= 0:
    st.error(f"⚠️ Quantity {qty} is below the exchange minimum ({min_qty}). Increase risk or widen your stop.")
    st.stop()

order_value = (qty * E).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
actual_risk = qty * distance
margin = qty * E / Decimal(leverage)
mmr = Decimal(str(mmr_pct)) / 100
pq = Decimal(1).scaleb(-price_dp)
tp = (E + distance * 3 if is_long else E - distance * 3).quantize(pq, rounding=ROUND_HALF_UP)

# Estimated liquidation: equity at liq = maintenance margin
B = margin if mode == "Isolated" else Decimal(str(balance))
if is_long:
    liq = (qty * E - B) / (qty * (1 - mmr))
    liq_safe = liq < SL
else:
    liq = (B + qty * E) / (qty * (1 + mmr))
    liq_safe = liq > SL
no_liq = is_long and liq <= 0

# Max leverage that keeps liquidation beyond SL (isolated)
denom = (1 - SL * (1 - mmr) / E) if is_long else (SL * (1 + mmr) / E - 1)
safe_max_lev = None if denom <= 0 else int(1 / denom)

# ============ STEP 4: COPY RESULTS ============
st.subheader("4. Copy into your exchange")
st.success("🟢 **LONG** (Stop Loss below Entry)") if is_long else st.error("🔴 **SHORT** (Stop Loss above Entry)")

a, b = st.columns(2)
with a:
    st.markdown("##### Order Value (USDT)")
    st.code(f"{order_value}", language=None)
    st.caption("Use if the exchange asks **Order by Value**")
with b:
    st.markdown("##### Order Qty (Coins)")
    st.code(f"{qty:f}", language=None)
    st.caption("Use if the exchange asks **Order by Qty**")

st.markdown(f"If your Stop Loss at **{SL:f}** is hit, you lose about **${actual_risk:,.2f}**. Use *either* Value *or* Qty, not both.")

# ============ SAFETY CHECK ============
st.subheader("Leverage check")
m1, m2, m3 = st.columns(3)
m1.metric("Margin required", f"${margin:,.2f}")
m2.metric(f"Est. liquidation ({mode})", "None" if no_liq else f"{liq:.{price_dp}f}")
m3.metric("Stop Loss", f"{SL:f}")

if margin > Decimal(str(balance)):
    st.error(f"❌ Margin needed (${margin:,.2f}) is more than your balance (${balance:,.2f}). Lower the risk or raise leverage "
             f"(and re-check liquidation).")
if no_liq or liq_safe:
    st.success("✅ Estimated liquidation is beyond your Stop Loss. The stop should trigger first.")
else:
    st.error("❌ Estimated liquidation is closer than your Stop Loss. You would be liquidated BEFORE the stop and lose more than your risk.")
    if mode == "Isolated" and safe_max_lev:
        st.warning(f"Lower leverage to about **{safe_max_lev}x or less** (or move your Stop Loss closer).")
if mode == "Isolated" and safe_max_lev and leverage <= safe_max_lev:
    st.caption(f"Highest leverage that keeps liquidation beyond your SL: about {safe_max_lev}x.")

with st.expander("Take Profit (1:3 R:R)"):
    st.code(f"{tp:f}", language=None)
    st.caption(f"Profit at 1:3 ≈ ${actual_risk * 3:,.2f}")

st.caption("⚠️ Liquidation is an estimate. The exchange's real figure depends on tiers, fees and funding. Always compare it with the liquidation price shown on the exchange's order panel. Fees and slippage add a little to the loss at the stop.")
