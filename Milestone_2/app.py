import streamlit as st
import pandas as pd
import plotly.express as px

# Load Data
df = pd.read_csv("data/raw/cleaned_weather_data.csv")

# Fix date column
df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")

st.set_page_config(page_title="Climate Dashboard", layout="wide")

st.markdown(
    """
    <h1 style='text-align:center; color:#4a90e2;'>🌍 Global Weather Insights Dashboard</h1>
    <p style='text-align:center; font-size:18px;'>Explore real-time weather patterns, compare regions, and analyze trends.</p>
    """,
    unsafe_allow_html=True
)

st.write("---")

# Select first 5 countries
countries = df["country"].unique()[:5]
filtered_df = df[df["country"].isin(countries)]

# Show the countries being displayed
st.markdown(f"**Countries Displayed:** {', '.join(countries)}")

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("🌡️ Average Temperature (°C)", round(filtered_df["temperature_celsius"].mean(), 2))
col2.metric("💧 Average Humidity (%)", round(filtered_df["humidity"].mean(), 2))
col3.metric("🌬️ Average Wind Speed (km/h)", round(filtered_df["wind_kph"].mean(), 2))

st.write("")

# Temperature Comparison Across Countries
st.subheader("📊 Temperature Comparison Across Countries")
fig_temp = px.bar(
    filtered_df,
    x="country",
    y="temperature_celsius",
    color="country",
    labels={"temperature_celsius": "Temperature (°C)"},
    title="Temperature by Country",
)
st.plotly_chart(fig_temp, use_container_width='stretch')

# Temperature vs Humidity
st.subheader("🌡️ Temperature vs 💧 Humidity")
fig_scatter = px.scatter(
    filtered_df,
    x="temperature_celsius",
    y="humidity",
    color="country",
    size="wind_kph",
    hover_name="country",
    title="Temperature vs Humidity",
)
st.plotly_chart(fig_scatter, use_container_width='stretch')

# Wind Speed Distribution
st.subheader("🍃 Wind Speed Distribution")
fig_wind = px.histogram(
    filtered_df,
    x="wind_kph",
    nbins=20,
    title="Wind Speed Distribution",
)
st.plotly_chart(fig_wind, use_container_width='stretch')

st.subheader("🗺️ Global Temperature Choropleth Map")

# Select first 10 countries
countries_10 = df["country"].unique()[:10]
filtered_df_10 = df[df["country"].isin(countries_10)]

# Compute average temperature per country
avg_temp_10 = (
    filtered_df_10.groupby("country")["temperature_celsius"]
    .mean()
    .reset_index()
)


# Choropleth Map
fig_choro = px.choropleth(
    avg_temp_10,
    locations="country",
    locationmode="country names",
    color="temperature_celsius",
    color_continuous_scale="Turbo",
    title="Average Temperature by Country",
    labels={"temperature_celsius": "Avg Temperature (°C)"}
)

st.plotly_chart(fig_choro, use_container_width='stretch')


