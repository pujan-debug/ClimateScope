import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="Climate Scope – Interactive Dashboard (Milestone 3)",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Climate Scope – Interactive Dashboard (Milestone 3)")

# -----------------------------------------------------
# LOAD DATA
# -----------------------------------------------------
DATA_PATH = "cleaned_weather_data.csv"     # <<== PUT YOUR DATA FILE HERE

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)

    # Standardize common datetime fields
    for col in df.columns:
        if col.lower() in ["date", "datetime", "timestamp", "last_updated"]:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Detect datetime column
    datetime_cols = [c for c in df.columns if df[c].dtype == 'datetime64[ns]']
    date_col = datetime_cols[0] if datetime_cols else None

    # Standardize country name column
    for col in df.columns:
        if col.lower() in ["country", "location", "country_name"]:
            df.rename(columns={col: "country"}, inplace=True)

    return df

df = load_data()

if df.empty:
    st.error("Dataset failed to load. Check your CSV file path.")
    st.stop()

# -----------------------------------------------------
# SIDEBAR FILTERS
# -----------------------------------------------------
st.sidebar.header("Filters")

# Detect date column
date_cols = [c for c in df.columns if "date" in c.lower() or df[c].dtype == "datetime64[ns]"]
date_col = date_cols[0] if date_cols else None

# COUNTRY FILTER
if "country" in df.columns:
    countries = sorted(df["country"].dropna().unique())
    selected_countries = st.sidebar.multiselect("Select Country", countries, default=countries[:3])
else:
    selected_countries = None

# PARAMETER FILTER
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
selected_param = st.sidebar.selectbox("Select Parameter", numeric_cols)

# AGGREGATION FILTER
agg_mode = st.sidebar.selectbox(
    "Aggregation",
    ["Raw Data", "Monthly Average", "Yearly Average"]
)

# DATE RANGE FILTER
if date_col:
    min_date = df[date_col].min()
    max_date = df[date_col].max()

    start, end = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date]
    )
else:
    start = end = None

# -----------------------------------------------------
# APPLY FILTERS
# -----------------------------------------------------
df_filtered = df.copy()

# Filter by country
if selected_countries:
    df_filtered = df_filtered[df_filtered["country"].isin(selected_countries)]

# Filter by date
if date_col and start and end:
    df_filtered = df_filtered[(df_filtered[date_col] >= pd.to_datetime(start)) &
                              (df_filtered[date_col] <= pd.to_datetime(end))]

# Apply aggregation
if agg_mode != "Raw Data" and date_col:
    df_filtered.set_index(date_col, inplace=True)
    if agg_mode == "Monthly Average":
        df_filtered = df_filtered.resample("M").mean().reset_index()
    elif agg_mode == "Yearly Average":
        df_filtered = df_filtered.resample("Y").mean().reset_index()

# -----------------------------------------------------
# KPI CARDS
# -----------------------------------------------------
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

if not df_filtered.empty:
    col1.metric("Minimum", f"{df_filtered[selected_param].min():.2f}")
    col2.metric("Maximum", f"{df_filtered[selected_param].max():.2f}")
    col3.metric("Mean", f"{df_filtered[selected_param].mean():.2f}")

    # Trend calculation
    try:
        first_val = df_filtered[selected_param].iloc[0]
        last_val = df_filtered[selected_param].iloc[-1]
        trend = ((last_val - first_val) / first_val) * 100 if first_val != 0 else 0
        col4.metric("Trend (%)", f"{trend:.2f}%")
    except:
        col4.metric("Trend (%)", "N/A")

else:
    st.warning("No data after applying filters.")
    st.stop()

# -----------------------------------------------------
# MAIN VISUALIZATIONS
# -----------------------------------------------------
st.subheader("Visualizations")

# 1. Time-Series Plot
if date_col:
    fig1 = px.line(
        df_filtered,
        x=date_col,
        y=selected_param,
        color="country" if "country" in df_filtered.columns else None,
        title=f"{selected_param} Over Time ({agg_mode})"
    )
    st.plotly_chart(fig1, use_container_width=True)

# 2. Box Plot (Distribution)
fig2 = px.box(
    df_filtered,
    y=selected_param,
    color="country" if "country" in df_filtered.columns else None,
    title=f"Distribution of {selected_param}"
)
st.plotly_chart(fig2, use_container_width=True)

# 3. Choropleth Map (if country available)
if "country" in df_filtered.columns:
    try:
        df_map = df_filtered.groupby("country")[selected_param].mean().reset_index()
        fig3 = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color=selected_param,
            title=f"World Map — Average {selected_param}"
        )
        st.plotly_chart(fig3, use_container_width=True)
    except:
        st.info("Map visualization skipped (country names might not match standard names).")

# 4. Monthly Heatmap (requires date)
if date_col:
    df_heat = df_filtered.copy()
    df_heat["Month"] = df_heat[date_col].dt.month
    df_heat["Year"] = df_heat[date_col].dt.year

    pivot = df_heat.pivot_table(
        values=selected_param,
        index="Year",
        columns="Month",
        aggfunc="mean"
    )

    fig4 = px.imshow(
        pivot,
        labels=dict(color=selected_param),
        aspect="auto",
        title="Monthly Heatmap"
    )
    st.plotly_chart(fig4, use_container_width=True)


# -----------------------------------------------------
# END OF APP
# -----------------------------------------------------
st.success("Dashboard updated successfully with all filters and visualizations.")
