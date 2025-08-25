import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

# It's good practice to keep the data fetching logic separate
from aqi_fetcher_python import get_aqi_data, get_aqi_description

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="AQI Dashboard", layout="wide")

st.title("Bangalore Air Quality Index (AQI) Dashboard")
st.markdown("This app fetches and displays historical AQI data from the OpenWeatherMap API.")

# Check for API key and guide the user if it's missing
if not os.getenv('OPENWEATHER_KEY'):
    st.error("`OPENWEATHER_KEY` not found.")
    st.info("Please create a `.env` file in the project root and add your API key:\n\n`OPENWEATHER_KEY='your_key_here'`")
    st.stop()

# --- Sidebar for User Inputs ---
st.sidebar.header("Settings")

# Note: The coordinates in the original script's example were swapped.
# These are the correct approximate coordinates for Bangalore.
lat = st.sidebar.number_input("Latitude", value=12.9716, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=77.5946, format="%.4f")
days = st.sidebar.slider("Number of days to analyze", 1, 30, 10)

if st.sidebar.button("Fetch AQI Data"):
    try:
        with st.spinner(f"Fetching data for the last {days} days..."):
            aqi_data = get_aqi_data(lat, lon, days)

        if not aqi_data:
            st.warning("No data returned from the API. Please check the coordinates and date range.")
        else:
            st.success("Data fetched successfully!")

            df = pd.DataFrame(aqi_data)
            # Convert date string to datetime object for better plotting
            df['date'] = pd.to_datetime(df['date'])

            # --- Main Page Display ---

            # Key Metrics
            st.header("Summary Statistics")
            avg_aqi = df['aqi'].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Average AQI", f"{avg_aqi:.1f}", get_aqi_description(round(avg_aqi)))

            best_day = df.loc[df['aqi'].idxmin()]
            col2.metric("Best Day (Lowest AQI)", f"{best_day['aqi']}", best_day['date'].strftime('%b %d, %Y'))

            worst_day = df.loc[df['aqi'].idxmax()]
            col3.metric("Worst Day (Highest AQI)", f"{worst_day['aqi']}", worst_day['date'].strftime('%b %d, %Y'))

            # AQI Trend Chart
            st.header("AQI Trend Over Time")
            fig_aqi = px.line(df, x='date', y='aqi', title='Daily Average AQI', markers=True,
                              labels={'aqi': 'Air Quality Index (AQI)', 'date': 'Date'},
                              hover_data={'aqi_description': True})
            fig_aqi.update_traces(hovertemplate='<b>%{x|%Y-%m-%d}</b><br>AQI: %{y}<br>Condition: %{customdata[0]}<extra></extra>')
            st.plotly_chart(fig_aqi, use_container_width=True)

            # Pollutant Levels Chart
            st.header("Pollutant Levels Over Time (μg/m³)")
            # Unpack the 'pollutants' dictionary into separate columns for easier plotting
            pollutants_df = pd.json_normalize(df['pollutants'])
            pollutants_df['date'] = df['date']

            # "Melt" the dataframe to a long format suitable for Plotly Express
            df_melted = pollutants_df.melt(id_vars=['date'], var_name='Pollutant', value_name='Concentration (μg/m³)')

            fig_pollutants = px.line(df_melted, x='date', y='Concentration (μg/m³)', color='Pollutant',
                                     title='Daily Average Pollutant Concentrations', markers=True)
            st.plotly_chart(fig_pollutants, use_container_width=True)

            # Raw Data expander
            with st.expander("View Raw Data"):
                st.dataframe(df)

    except Exception as e:
        st.error(f"An error occurred while fetching data: {e}")
else:
    st.info("Adjust the settings in the sidebar and click 'Fetch AQI Data' to begin.")
