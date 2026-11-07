import streamlit as st

st.set_page_config(page_title="Universal Position Calculator", page_icon="📊", layout="centered")

st.title("📊 Universal Risk & Position Size Calculator")
st.caption("Built by Salam Afeez | Financial Data Analyst & Risk Modeling")

st.markdown("---")

# User Inputs in two clean columns
col1, col2 = st.columns(2)

with col1:
    account_balance = st.number_input("Account Balance ($)", min_value=10.0, value=10000.0, step=100.0)
    risk_percent = st.number_input("Risk per Trade (%)", min_value=0.1, max_value=100.0, value=1.0, step=0.25)
    rr_ratio = st.number_input("Target Risk-to-Reward (1 : X)", min_value=0.5, value=3.0, step=0.5)

with col2:
    entry_price = st.number_input("Entry Price", min_value=0.00001, value=1.08500, format="%.5f")
    stop_loss = st.number_input("Stop Loss Price", min_value=0.00001, value=1.08200, format="%.5f")
    contract_size = st.selectbox(
        "Asset Class / Contract Size",
        options=[
            ("Crypto / Indices / Stocks (1 Unit)", 1),
            ("Standard FX Lot (100,000 Units)", 100000),
            ("Mini FX Lot (10,000 Units)", 10000),
        ],
        format_func=lambda x: x[0]
    )[1]

st.markdown("---")

# Core Mathematical Engine
risk_dollars = account_balance * (risk_percent / 100.0)
stop_distance = abs(entry_price - stop_loss)

if stop_distance == 0:
    st.error("⚠️ Entry Price and Stop Loss cannot be identical. Please adjust your Stop Loss.")
else:
    # Trade Direction & Target Calculation
    is_long = entry_price > stop_loss
    direction = "🟢 LONG (BUY)" if is_long else "🔴 SHORT (SELL)"
    take_profit = entry_price + (stop_distance * rr_ratio) if is_long else entry_price - (stop_distance * rr_ratio)
    expected_reward = risk_dollars * rr_ratio

    # Universal Position Size Formula
    raw_units = risk_dollars / stop_distance
    position_lots = raw_units / contract_size

    # Output Metrics Display
    st.subheader(f"Trade Setup: {direction}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Capital at Risk", f"${risk_dollars:,.2f}", f"-{risk_percent}%")
    m2.metric("Required Units", f"{raw_units:,.2f}")
    m3.metric("Position Size (Lots/Contracts)", f"{position_lots:,.4f}")

    m4, m5, m6 = st.columns(3)
    m4.metric("Stop Distance", f"{stop_distance:.5f}")
    m5.metric(f"Take Profit (1:{rr_ratio:g})", f"{take_profit:.5f}")
    m6.metric("Projected Profit", f"${expected_reward:,.2f}", f"+{risk_percent * rr_ratio:g}%")
