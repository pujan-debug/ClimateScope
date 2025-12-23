import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    page_title="ClimateScope Dashboard",
    layout="wide"
)


# DATA LOADING & CLEANING

@st.cache_data
def load_data():
    df = pd.read_csv("data/raw/cleaned_weather_data.csv")

   
    df.rename(columns={
        "temp_c": "temperature_celsius",
        "wind_kph": "wind_kph",
        "precip_mm": "precip_mm"
    }, inplace=True)

    # Date handling
    df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")
    df.dropna(subset=["last_updated"], inplace=True)

    return df

df = load_data()

df["last_updated"] = pd.to_datetime(
    df["last_updated"],
    errors="coerce",
    infer_datetime_format=True
)

# Remove invalid dates
df = df.dropna(subset=["last_updated"])



# SIDEBAR – NAVIGATION

st.sidebar.title("🌍 ClimateScope")
page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Dashboard",
        "Statistical Analysis",
        "Climate Trends",
        "Extreme Events",
        "Infrastructure Risk Management",
        "Help & User Guide"
    ]
)


# SIDEBAR – GLOBAL FILTERS

st.sidebar.header("Global Filters")

# Country filter
countries = sorted(df["country"].unique())
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    countries,
    
)

if len(selected_countries) == 0:
    selected_countries = countries


# --- DATE FILTER  ---
min_date = df["last_updated"].min().date()
max_date = df["last_updated"].max().date()


date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Convert back to datetime
start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1])


# Metric selector
metric = st.sidebar.selectbox(
    "Select Metric",
    [
        "temperature_celsius",
        "humidity",
        "precip_mm",
        "wind_kph"
    ]
)

# Time aggregation
aggregation = st.sidebar.selectbox(
    "Time Aggregation",
    ["Monthly", "Seasonal"]
)

# Normalization
normalize = st.sidebar.checkbox("Normalize Metric")

# Extreme threshold
threshold = st.sidebar.number_input(
    "Extreme Event Threshold",
    value=35.0
)


# DATA FILTERING

filtered_df = df[
    (df["country"].isin(selected_countries)) &
    (df["last_updated"] >= start_date) &
    (df["last_updated"] <= end_date)
].copy()

# INFRASTRUCTURE RISK INDEX CALCULATION


filtered_df["infrastructure_risk_score"] = (
    filtered_df["temperature_celsius"] * 0.4 +
    filtered_df["precip_mm"] * 0.35 +
    filtered_df["wind_kph"] * 0.25
)
filtered_df["risk_index"] = filtered_df["infrastructure_risk_score"]

def classify_risk(score):
    if score < 10:
        return "Low Risk"
    elif score < 12:
        return "Moderate Risk"
    else:
        return "High Risk"

filtered_df["risk_level"] = filtered_df["risk_index"].apply(classify_risk)


filtered_df["last_updated"] = pd.to_datetime(filtered_df["last_updated"])
if aggregation == "Monthly":

    agg_df = (
        filtered_df
        .groupby(["country", pd.Grouper(key="last_updated", freq="MS")])[metric]
        .mean()
        .reset_index()
    )

    x_axis = "last_updated"



elif aggregation == "Seasonal":

    filtered_df["year"] = filtered_df["last_updated"].dt.year
    filtered_df["season"] = filtered_df["last_updated"].dt.month.map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Autumn", 10: "Autumn", 11: "Autumn"
    })

    agg_df = (
        filtered_df
        .groupby(["country", "year", "season"])[metric]
        .mean()
        .reset_index()
    )

    # Create sortable seasonal timeline
    agg_df["season_order"] = agg_df["season"].map(
        {"Winter": 1, "Spring": 2, "Summer": 3, "Autumn": 4}
    )

    agg_df["season_time"] = (
        agg_df["year"].astype(str) + "-" + agg_df["season"]
    )

    x_axis = "season_time"


else:  # Daily (cleaned)

    agg_df = (
        filtered_df
        .groupby(["country", "last_updated"])[metric]
        .mean()
        .reset_index()
    )

    x_axis = "last_updated"

# Normalization
if normalize:
    agg_df[metric] = (
        agg_df[metric] - agg_df[metric].mean()
    ) / agg_df[metric].std()

# EXECUTIVE DASHBOARD

if page == "Executive Dashboard":

    st.title("📊 Executive Climate Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Global Mean Temp (°C)", round(filtered_df["temperature_celsius"].mean(), 2))
    col2.metric("Avg Humidity (%)", round(filtered_df["humidity"].mean(), 2))
    col3.metric("Total Records", len(filtered_df))

    st.subheader("🌍 Global Temperature Map")

    map_df = (
        filtered_df.groupby("country")["temperature_celsius"]
        .mean().reset_index()
    )

    fig_map = px.choropleth(
        map_df,
        locations="country",
        locationmode="country names",
        color="temperature_celsius",
        hover_name="country",
        title="Average Temperature by Country"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("📈 Climate Trend Snapshot")

    fig_bar = px.bar(
    agg_df,
    x=x_axis,
    y=metric,
    color="country",
    barmode="group",
    title=f"{metric} Trend by Country"
)

    fig_bar.update_layout(
    xaxis_title="Time",
    yaxis_title=metric.replace("_", " ").title(),
    legend_title="Country"
)

    st.plotly_chart(fig_bar, use_container_width=True)



# STATISTICAL ANALYSIS

elif page == "Statistical Analysis":

    st.title("📉 Statistical Analysis")

    st.subheader("Correlation Heatmap")
    corr = filtered_df[
        ["temperature_celsius", "humidity", "precip_mm", "wind_kph"]
    ].corr()

    fig_corr = px.imshow(corr, text_auto=True)
    st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Metric Distribution")

    fig_hist = px.histogram(
        filtered_df,
        x=metric,
        color="country",
        marginal="box"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("Descriptive Statistics")
    st.dataframe(filtered_df.describe())


# CLIMATE TRENDS

elif page == "Climate Trends":

    st.title("📈 Climate Trends Analysis")

    st.subheader("Line & Area Charts")
    fig_area = px.area(
        agg_df,
        x=x_axis,
        y=metric,
        color="country"
    )
    st.plotly_chart(fig_area, use_container_width=True)

    st.subheader("Violin Plot")
    fig_violin = px.violin(
        filtered_df,
        y=metric,
        x="country",
        box=True
    )
    st.plotly_chart(fig_violin, use_container_width=True)

    st.subheader("Box Plot")
    fig_box = px.box(
        filtered_df,
        x="country",
        y=metric
    )
    st.plotly_chart(fig_box, use_container_width=True)


# EXTREME EVENTS

elif page == "Extreme Events":

    st.title("🔥 Extreme Events Analysis")

    extreme_df = filtered_df[filtered_df[metric] >= threshold]

    st.subheader("Top 5 Extreme Events")
    st.dataframe(
        extreme_df.sort_values(metric, ascending=False)
        .head(5)[["country", "last_updated", metric]]
    )

    st.subheader("Extreme Events Frequency")
    extreme_df["month"] = extreme_df["last_updated"].dt.to_period("M").astype(str)

    freq_df = extreme_df.groupby("month").size().reset_index(name="count")

    fig_freq = px.bar(freq_df, x="month", y="count")
    st.plotly_chart(fig_freq, use_container_width=True)
  
# INFRASTRUCTURE RISK MANAGEMENT


elif page == "Infrastructure Risk Management":

    st.title("🏗 Infrastructure Risk Management")

    st.markdown("""
    This section translates climate conditions into **infrastructure risk insights**
    to support planning, resilience, and mitigation strategies.
    """)

    # KPI Metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Average Risk Index",
        round(filtered_df["risk_index"].mean(), 2)
    )

    col2.metric(
        "High Risk Events",
        (filtered_df["risk_level"] == "High Risk").sum()
    )

    col3.metric(
        "Countries Selected",
        len(selected_countries)
    )

    # RISK MAP (CHANGES BY COUNTRY SELECTION)
  

    st.subheader("🌍 Infrastructure Risk by Country")

    risk_map_df = (
        filtered_df
        .groupby("country")["risk_index"]
        .mean()
        .reset_index()
    )

    fig_risk_map = px.choropleth(
        risk_map_df,
        locations="country",
        locationmode="country names",
        color="risk_index",
        color_continuous_scale="Reds",
        title="Average Infrastructure Risk Index"
    )

    st.plotly_chart(fig_risk_map, use_container_width=True)

    # RISK TREND (SINGLE OR MULTI-COUNTRY)
  

    st.subheader("📈 Infrastructure Risk Trend")

    trend_df = (
        filtered_df
        .set_index("last_updated")
        .groupby("country")["risk_index"]
        .resample("MS")
        .mean()
        .reset_index()
    )

    fig_trend = px.line(
        trend_df,
        x="last_updated",
        y="risk_index",
        color="country",
        title="Monthly Infrastructure Risk Trend"
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    
    # HIGH RISK EVENTS TABLE
   

    st.subheader("🔥 High Risk Infrastructure Events")

    high_risk_df = filtered_df[filtered_df["risk_level"] == "High Risk"]

    if high_risk_df.empty:
        st.info("No high-risk events detected for the selected filters.")
    else:
        st.dataframe(
            high_risk_df.sort_values("risk_index", ascending=False)
            .head(10)[
                ["country", "last_updated", "risk_index", "risk_level"]
            ]
        )

  
    # RISK DISTRIBUTION
  

    st.subheader("📊 Risk Level Distribution")

    risk_dist = (
        filtered_df
        .groupby("risk_level")
        .size()
        .reset_index(name="count")
    )

    fig_pie = px.pie(
        risk_dist,
        names="risk_level",
        values="count",
        title="Infrastructure Risk Distribution"
    )

    st.plotly_chart(fig_pie, use_container_width=True)


# HELP SECTION

else:

    st.title("ℹ️ Help & User Guide")

    st.markdown("""
    **ClimateScope Dashboard Features**

    • Multi-country and date filtering  
    • Interactive charts with zoom & hover  
    • Extreme weather detection  
    • Statistical and seasonal analysis  
    • Downloadable Plotly charts  

    **Usage Tips**
    - Use sidebar to control filters
    - Hover over charts for details
    - Use Plotly toolbar to export PNG
    """)


# FOOTER

st.markdown("---")
st.caption("ClimateScope  |  Analysis of current climate data trends and extreme events.")
