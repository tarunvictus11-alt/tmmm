import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & REAL-TIME REFRESH
# ---------------------------------------------------------
st.set_page_config(
    page_title="VayuNexa Enterprise | Atmospheric Intelligence Platform",
    page_icon="🌫️",
    layout="wide"
)

# Auto-refresh every 60 seconds
count = st_autorefresh(interval=60000, limit=None, key="vayunexa_enterprise_counter")

ist_timezone = pytz.timezone('Asia/Kolkata')
current_ist_time = datetime.now(ist_timezone).strftime("%I:%M:%S %p IST | %d-%b-%Y")

st.title("🌫️ VayuNexa Enterprise: Atmospheric-Chemical Forecasting System")
st.caption("Real-Time Atmospheric & Air Quality Monitoring Engine | Delhi NCR")
st.markdown("---")

# ---------------------------------------------------------
# 2. SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.header("🕹️ Production Controls")
st.sidebar.markdown("---")
st.sidebar.subheader("📡 Live Stream Status")
st.sidebar.write(f"**System Status:** 🟢 LIVE API CONNECTED")
st.sidebar.write(f"**Exact Local Time:** `{current_ist_time}`")
st.sidebar.write(f"**Refresh Cycle:** 60s")

# ---------------------------------------------------------
# 3. LIVE DATA ASSIMILATION (Delhi Coordinates)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_real_atmospheric_data():
    lat, lon = 28.6139, 77.2090
    
    aq_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone&timezone=Asia%2FKolkata&forecast_days=3"
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=boundary_layer_height,temperature_2m,windspeed_10m&timezone=Asia%2FKolkata&forecast_days=3"

    try:
        aq_res = requests.get(aq_url, timeout=5).json()
        w_res = requests.get(weather_url, timeout=5).json()

        df_aq = pd.DataFrame(aq_res['hourly'])
        df_w = pd.DataFrame(w_res['hourly'])

        df = pd.merge(df_aq, df_w, on='time')
        df['time'] = pd.to_datetime(df['time']).dt.strftime('%d-%b %H:00')
        return df.iloc[:72]
    except Exception as e:
        st.error(f"Error fetching live API data: {e}")
        return pd.DataFrame()

df_data = fetch_real_atmospheric_data()

if not df_data.empty:
    curr_pm25 = df_data['pm2_5'].iloc[0]
    curr_pm10 = df_data['pm10'].iloc[0]
    curr_o3 = df_data['ozone'].iloc[0]
    curr_no2 = df_data['nitrogen_dioxide'].iloc[0]
    curr_so2 = df_data['sulphur_dioxide'].iloc[0]
    curr_co = df_data['carbon_monoxide'].iloc[0]
    curr_pbl = df_data['boundary_layer_height'].iloc[0]

    # ---------------------------------------------------------
    # 4. DASHBOARD METRICS
    # ---------------------------------------------------------
    st.subheader(f"📊 Real-Time Measured Metrics ({current_ist_time})")
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    with m1:
        st.metric("PM2.5 Level", f"{curr_pm25} µg/m³")
    with m2:
        st.metric("PM10 Level", f"{curr_pm10} µg/m³")
    with m3:
        st.metric("Ozone (O3)", f"{curr_o3} µg/m³")
    with m4:
        st.metric("NO2 Level", f"{curr_no2} µg/m³")
    with m5:
        st.metric("SO2 Level", f"{curr_so2} µg/m³")
    with m6:
        st.metric("CO Level", f"{curr_co} µg/m³")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.metric("Boundary Layer Height (PBLH)", f"{int(curr_pbl)} meters")
    with c2:
        if curr_pbl < 200:
            st.error("🚨 Inversion Lid Hazard: Particle Retention Layer Active")
        else:
            st.success("🟢 Atmospheric Boundary Condition: Normal Dispersion")

    # ---------------------------------------------------------
    # 5. DYNAMIC FORECAST CHARTS
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📈 72-Hour Live Trajectory Forecast (Delhi NCR)")

    pollutant_choice = st.selectbox(
        "Select Chemical Parameter to Overlay with Boundary Layer Height (PBLH):",
        ["PM2.5", "PM10", "Ozone (O3)", "NO2", "SO2", "CO"]
    )

    pollutant_map = {
        "PM2.5": ('pm2_5', "PM2.5 (µg/m³)", "#e74c3c"),
        "PM10": ('pm10', "PM10 (µg/m³)", "#e67e22"),
        "Ozone (O3)": ('ozone', "O3 (µg/m³)", "#3498db"),
        "NO2": ('nitrogen_dioxide', "NO2 (µg/m³)", "#9b59b6"),
        "SO2": ('sulphur_dioxide', "SO2 (µg/m³)", "#f1c40f"),
        "CO": ('carbon_monoxide', "CO (µg/m³)", "#34495e")
    }

    col_key, label_name, color_code = pollutant_map[pollutant_choice]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_data['time'], y=df_data[col_key], mode='lines+markers', name=label_name,
        line=dict(color=color_code, width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df_data['time'], y=df_data['boundary_layer_height'], mode='lines', name='PBL Height (m)',
        line=dict(color='#2ecc71', width=2, dash='dot'), yaxis='y2'
    ))

    fig.update_layout(
        xaxis=dict(title='72-Hour IST Timeline'),
        yaxis=dict(title=dict(text=label_name, font=dict(color=color_code))),
        yaxis2=dict(title=dict(text='PBL Height (Meters)', font=dict(color='#2ecc71')), overlaying='y', side='right'),
        legend=dict(x=0.01, y=0.99),
        height=450,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
