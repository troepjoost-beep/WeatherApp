import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from geopy.geocoders import Nominatim
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="Weather Year-over-Year", layout="wide")
st.title("🌦️ Weather Comparison Dashboard")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Search Parameters")
    city_name = st.text_input("Enter City", value="Malaga")
    
    today = datetime.now()
    date_range = st.date_input(
        "Select Date Range (Day/Month)",
        value=(datetime(today.year, 9, 1), datetime(today.year, 10, 30))
    )
    
    selected_year = st.selectbox("Compare Year", options=[2025, 2024, 2023, 2022], index=0)

# --- Updated Helper Function with Error Handling ---
def get_location_details(city):
    """Returns (lat, lon, display_name) or (None, None, None) if not found"""
    geolocator = Nominatim(user_agent="weather_app_comparison_v2")
    try:
        # language="en" ensures the country name is readable regardless of local naming
        location = geolocator.geocode(city, language="en", addressdetails=True)
        if location:
            address = location.raw.get('address', {})
            country = address.get('country', 'Unknown Country')
            # Create a nice string like "Malaga, Andalusia, Spain"
            display_name = f"{location.address}"
            return location.latitude, location.longitude, display_name
        return None, None, None
    except Exception:
        return None, None, None

def fetch_weather(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "auto"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["daily"])
        df['time'] = pd.to_datetime(df['time'])
        return df
    return None

# --- Main App Logic ---
if len(date_range) == 2:
    start_dt, end_dt = date_range
    target_start = start_dt.replace(year=selected_year)
    target_end = end_dt.replace(year=selected_year)
    
    # 1. Look up the city
    lat, lon, full_address = get_location_details(city_name)
    
    if lat:
        # 2. Show the confirmed location to the user
        st.success(f"📍 **Location Confirmed:** {full_address}")
        
        with st.spinner(f"Loading weather data for {selected_year}..."):
            df = fetch_weather(lat, lon, target_start, target_end)
            
            if df is not None:
                # --- Visualization ---
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['time'], y=df['temperature_2m_max'], name="Max Temp (°C)", line=dict(color='firebrick', width=3)))
                fig.add_trace(go.Scatter(x=df['time'], y=df['temperature_2m_min'], name="Min Temp (°C)", line=dict(color='royalblue', width=3)))
                fig.add_trace(go.Bar(x=df['time'], y=df['precipitation_sum'], name="Rain (mm)", marker_color='lightblue', opacity=0.6, yaxis="y2"))

                fig.update_layout(
                    title=f"Weather Trends in {selected_year}",
                    xaxis_title="Date",
                    yaxis=dict(title="Temperature (°C)"),
                    yaxis2=dict(title="Precipitation (mm)", overlaying="y", side="right"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary Stats
                c1, c2, c3 = st.columns(3)
                c1.metric("Peak Temp", f"{df['temperature_2m_max'].max()} °C")
                c2.metric("Lowest Temp", f"{df['temperature_2m_min'].min()} °C")
                c3.metric("Total Rain", f"{df['precipitation_sum'].sum():.1f} mm")
    else:
        # 3. Specific Error for "Not Found"
        st.error(f"🔍 **Error:** Could not find a city named '{city_name}'. Please check the spelling or add a country (e.g., 'Malaga, Spain').")
else:
    st.info("Please select a complete date range in the sidebar.")