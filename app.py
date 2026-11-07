import streamlit as st

st.set_page_config(page_title="Universal Crypto Position Calculator", page_icon="⚡", layout="centered")

st.title("⚡ Universal Crypto Futures Position Calculator")
st.caption("Bybit / Bitget Hedge Mode Order Value & Quantity | Built by Salam Afeez")

st.markdown("---")

# 1. Your 3 Exact Inputs (Defaulted to your Excel / Jupyter values)
col1, col2, col3 = st.columns(3)

with col1:
    entry_price = st.number_input("Entry Price (E)", min_value=0.0000001, value=0.87718, step=0.00010, format="%.5f")

with col2:
    stop_loss = st.number_input("Stop Loss (SL)", min_value=0.0000001, value=0.87678, step=0.00010, format="%.5f")

with col3:
    risk_dollars = st.number_input("Risk ($ USDT)", min_value=0.1, value=100.0, step=1.0, format="%.2f")

st.markdown("---")

# 2. Find the price gap between Entry and Stop Loss
stop_distance = abs(entry_price - stop_loss)

if stop_distance == 0:
    st.error("⚠️ Entry Price and Stop Loss cannot be identical.")
else:
    # 3. Calculate how many coins/tokens you are buying or shorting
    coin_quantity = risk_dollars / stop_distance

    # 4. YOUR UNIVERSAL FORMULA: Convert coin quantity into USDT Order Value
    order_value = coin_quantity * entry_price

    # 5. Automatically detect Long vs. Short and calculate 1:3 Take-Profit
    if entry_price > stop_loss:
        direction = "🟢 LONG"
        take_profit_1_to_3 = entry_price + (stop_distance * 3)
    else:
        direction = "🔴 SHORT"
        take_profit_1_to_3 = entry_price - (stop_distance * 3)

    expected_profit_1_to_3 = risk_dollars * 3

    # 6. Display the clean results
    st.subheader(f"Trade Direction: {direction}")

    # Primary Copy-Paste Box for Bybit / Bitget
    st.success(
        f"**Order Value (USDT):** `${order_value:,.0f}` *(Exact: ${order_value:,.2f})* \n"
        f"**Position Size (Coins):** `{coin_quantity:,.0f} units`  \n"
        f"**Take Profit (1:3 R:R):** `{take_profit_1_to_3:.5f}` *(+${expected_profit_1_to_3:,.2f})*"
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Order Value (USDT)", f"${order_value:,.0f}")
    m2.metric("Position Size (Coins)", f"{coin_quantity:,.0f}")
    m3.metric("Take Profit (1:3)", f"{take_profit_1_to_3:.5f}")

    m4, m5, m6 = st.columns(3)
    m4.metric("Entry Price", f"{entry_price:.5f}")
    m5.metric("Stop Loss", f"{stop_loss:.5f}")
    m6.metric("Risk ($)", f"${risk_dollars:,.2f}")
