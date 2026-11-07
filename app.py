import streamlit as st
from decimal import Decimal, ROUND_DOWN

st.set_page_config(page_title="Position Size Calculator", page_icon="⚡", layout="centered")
st.title("⚡ Position Size Calculator")
st.caption("Works on any exchange and any coin • Built by Salam Afeez")

# ---------- INPUTS ----------
c1, c2, c3 = st.columns(3)
with c1:
    entry_price = st.number_input("Entry Price", min_value=0.0, value=0.87718, step=0.0001, format="%.6f")
with c2:
    stop_loss = st.number_input("Stop Loss", min_value=0.0, value=0.87678, step=0.0001, format="%.6f")
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

# Auto rounding (always DOWN so you never risk more than you set)
if raw_qty >= 100:
    qty_decimals = 0
elif raw_qty >= 10:
    qty_decimals = 1
elif raw_qty >= 1:
    qty_decimals = 2
elif raw_qty >= 0.1:
    qty_decimals = 3
else:
    qty_decimals = 4

step = Decimal(1).scaleb(-qty_decimals)
qty = (raw_qty // step) * step
if qty <= 0:
    st.error("⚠️ Quantity is too small. Increase risk or widen your stop.")
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
    leverage = l1.number_input("Leverage (x)", min_value=1, max_value=500, value=20, step=1)
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
                               step=0.0001, format="%.6f")
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
