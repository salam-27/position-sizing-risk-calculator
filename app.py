import streamlit as st
import requests
from decimal import Decimal, ROUND_DOWN

st.set_page_config(page_title="Position Size Calculator", page_icon="⚡", layout="centered")
st.title("⚡ Position Size Calculator")
st.caption("Works on any exchange and any coin • Built by Salam Afeez")

# ---------- TOP 300 COINS (optional helper) ----------
@st.cache_data(ttl=300)
def load_coins():
    base = "https://api.bitget.com/api/v2/mix/market"
    t = requests.get(f"{base}/tickers", params={"productType": "USDT-FUTURES"}, timeout=10).json()["data"]
    c = requests.get(f"{base}/contracts", params={"productType": "USDT-FUTURES"}, timeout=10).json()["data"]
    meta = {x["symbol"]: x for x in c}
    rows = []
    for x in t:
        m = meta.get(x["symbol"])
        if not m or m.get("symbolStatus", "normal") != "normal":
            continue
        step = m.get("sizeMultiplier") or str(Decimal(1).scaleb(-int(m["volumePlace"])))
        rows.append(dict(
            symbol=x["symbol"],
            price=float(x["lastPr"]),
            vol=float(x.get("usdtVolume") or x.get("quoteVolume") or 0),
            price_dp=int(m["pricePlace"]),
            qty_step=str(step),
            min_qty=str(m.get("minTradeNum", step)),
            max_lev=int(float(m.get("maxLever", 125))),
        ))
    rows.sort(key=lambda r: r["vol"], reverse=True)
    return rows[:300]

MANUAL = "Any coin (type prices manually)"

def on_coin_change():
    p = st.session_state.get("_lookup", {}).get(st.session_state.coin)
    if p:
        st.session_state.entry = p["price"]
        st.session_state.sl = round(p["price"] * 0.995, p["price_dp"])

if "coin" not in st.session_state:
    st.session_state.coin = MANUAL
    st.session_state.entry = 0.87718
    st.session_state.sl = 0.87678

try:
    coins = load_coins()
    load_failed = False
except Exception:
    coins, load_failed = [], True

lookup = {p["symbol"]: p for p in coins}
st.session_state["_lookup"] = lookup

st.selectbox("Coin (optional, type to search)", [MANUAL] + list(lookup.keys()),
             key="coin", on_change=on_coin_change)
if load_failed:
    st.caption("Coin list unavailable right now. Manual mode works normally.")

pair = lookup.get(st.session_state.coin)
price_dp = pair["price_dp"] if pair else 6
max_lev = pair["max_lev"] if pair else 500
if pair:
    st.caption(f"Live price {pair['price']} • Min qty {pair['min_qty']} • Max leverage {pair['max_lev']}x")

# ---------- INPUTS ----------
c1, c2, c3 = st.columns(3)
with c1:
    entry_price = st.number_input("Entry Price", min_value=0.0, step=10 ** (-price_dp),
                                  format=f"%.{price_dp}f", key="entry")
with c2:
    stop_loss = st.number_input("Stop Loss", min_value=0.0, step=10 ** (-price_dp),
                                format=f"%.{price_dp}f", key="sl")
with c3:
    risk_dollars = st.number_input("Risk (USDT)", min_value=0.1, value=100.0, step=1.0, format="%.2f")

# ---------- CALCULATION ----------
E, SL, R = Decimal(str(entry_price)), Decimal(str(stop_loss)), Decimal(str(risk_dollars))
distance = abs(E - SL)
st.divider()

if E <= 0 or SL <= 0 or distance == 0:
    st.error("⚠️ Enter a valid Entry and Stop Loss (they cannot be the same).")
    st.stop()

is_long = E > SL
raw_qty = R / distance

if pair:
    step = Decimal(pair["qty_step"])
    min_qty = Decimal(pair["min_qty"])
else:
    # auto rounding for manual mode
    if raw_qty >= 100:
        d = 0
    elif raw_qty >= 10:
        d = 1
    elif raw_qty >= 1:
        d = 2
    elif raw_qty >= 0.1:
        d = 3
    else:
        d = 4
    step = Decimal(1).scaleb(-d)
    min_qty = Decimal(0)

qty = (raw_qty // step) * step   # always rounds DOWN
if qty <= 0 or qty < min_qty:
    st.error(f"⚠️ Quantity is below the minimum order size ({min_qty}). Increase risk or widen your stop.")
    st.stop()

order_value = (qty * E).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
actual_risk = qty * distance

# ---------- RESULTS ----------
if is_long:
    st.success("🟢 **LONG**")
else:
    st.error("🔴 **SHORT**")

a, b = st.columns(2)
with a:
    st.markdown("##### Order Value (USDT)")
    st.code(f"{order_value}", language=None)
with b:
    st.markdown("##### Order Qty (Coins)")
    st.code(f"{qty:f}", language=None)

st.write(f"Use **either** one. If your Stop Loss is hit, you lose about **${actual_risk:,.2f}**.")

# ---------- OPTIONAL: LEVERAGE CHECK ----------
with st.expander("📊 Leverage & liquidation check (optional)"):
    l1, l2 = st.columns(2)
    leverage = l1.number_input(f"Leverage (x) — max {max_lev}x", min_value=1, max_value=max_lev,
                               value=min(20, max_lev), step=1)
    mode = l2.radio("Margin mode", ["Isolated", "Cross"], horizontal=True)
    l3, l4 = st.columns(2)
    balance = l3.number_input("Futures balance (USDT)", min_value=0.0, value=1000.0, step=50.0)
    mmr = Decimal(str(l4.number_input("Maintenance margin (%)", 0.0, 5.0, 0.5, 0.1))) / 100

    margin = qty * E / Decimal(leverage)
    B = margin if mode == "Isolated" else Decimal(str(balance))
    if is_long:
        liq = (qty * E - B) / (qty * (1 - mmr))
        safe = liq < SL
    else:
        liq = (B + qty * E) / (qty * (1 + mmr))
        safe = liq > SL

    m1, m2 = st.columns(2)
    m1.metric("Margin required", f"${margin:,.2f}")
    m2.metric("Est. liquidation", "None" if liq <= 0 else f"{liq:.6g}")

    if margin > Decimal(str(balance)):
        st.error("❌ Margin needed is more than your balance.")
    if safe or liq <= 0:
        st.success("✅ Liquidation is beyond your Stop Loss.")
    else:
        denom = (1 - SL * (1 - mmr) / E) if is_long else (SL * (1 + mmr) / E - 1)
        tip = f" Try {int(1 / denom)}x or lower." if denom > 0 and mode == "Isolated" else ""
        st.error(f"❌ You'd be liquidated BEFORE your Stop Loss.{tip}")

    st.caption("Leverage never changes the order size or the risk at your stop. It changes the margin locked and "
               "how close liquidation is. Isolated = only this trade's margin is at risk. Cross = your whole "
               "futures balance backs the trade, so liquidation is further away but losses can be bigger. "
               "Estimate only; check the exchange's liquidation price.")

# ---------- OPTIONAL: TAKE PROFIT (user's own target) ----------
with st.expander("🎯 Take Profit / expected return (optional)"):
    tp_input = st.number_input("Take Profit price (leave 0 to skip)", min_value=0.0, value=0.0,
                               step=10 ** (-price_dp), format=f"%.{price_dp}f")
    if tp_input > 0:
        TP = Decimal(str(tp_input))
        valid = TP > E if is_long else TP < E
        if not valid:
            direction = "above" if is_long else "below"
            st.error(f"⚠️ For a {'LONG' if is_long else 'SHORT'}, Take Profit must be {direction} Entry.")
        else:
            profit = qty * abs(TP - E)
            rr = profit / actual_risk
            move_pct = abs(TP - E) / E * 100
            roi = profit / margin * 100

            t1, t2, t3 = st.columns(3)
            t1.metric("Estimated profit", f"${profit:,.2f}")
            t2.metric("Risk : Reward", f"1 : {rr:.2f}")
            t3.metric("Return on margin", f"{roi:,.1f}%")
            st.caption(f"Price moves {move_pct:.2f}% to reach your target. Return on margin uses the leverage "
                       f"set above ({leverage}x). Estimates are before fees and funding.")
