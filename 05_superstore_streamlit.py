"""
## 📊 SUPERSTORE SALES FORECASTING DASHBOARD
Interactive dashboard for sales forecasting
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os

# Page configuration
st.set_page_config(
    page_title="Superstore Sales Forecast",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Superstore Sales Forecasting Dashboard")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/cleaned_superstore_sales.csv')
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    return df

@st.cache_data
def load_forecast():
    if os.path.exists('reports/final_7day_forecast.csv'):
        forecast = pd.read_csv('reports/final_7day_forecast.csv')
        forecast['Date'] = pd.to_datetime(forecast['Date'])
        return forecast
    else:
        return None

try:
    df = load_data()
    forecast = load_forecast()

    # Sidebar
    st.sidebar.header("🔍 Filters")

    # Date range filter
    min_date = df['Order Date'].min()
    max_date = df['Order Date'].max()
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Region filter
    regions = ['All'] + sorted(df['Region'].unique())
    selected_region = st.sidebar.selectbox("Select Region", regions)

    # Category filter
    categories = ['All'] + sorted(df['Category'].unique())
    selected_category = st.sidebar.selectbox("Select Category", categories)

    # Filter data
    filtered_df = df.copy()
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['Order Date'] >= pd.to_datetime(date_range[0])) &
            (filtered_df['Order Date'] <= pd.to_datetime(date_range[1]))
        ]
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['Region'] == selected_region]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]

    # Key Metrics
    st.header("📈 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_sales = filtered_df['Sales'].sum()
        st.metric("Total Sales", f"${total_sales:,.0f}")

    with col2:
        total_profit = filtered_df['Profit'].sum()
        st.metric("Total Profit", f"${total_profit:,.0f}")

    with col3:
        avg_profit_margin = filtered_df['Profit_Margin'].mean()
        st.metric("Avg Profit Margin", f"{avg_profit_margin:.1f}%")

    with col4:
        total_orders = len(filtered_df)
        st.metric("Total Orders", f"{total_orders:,}")

    st.markdown("---")

    # Sales Trend
    st.header("📊 Sales Trend Analysis")
    col1, col2 = st.columns(2)

    with col1:
        # Monthly sales trend
        monthly_sales = filtered_df.groupby(filtered_df['Order Date'].dt.to_period('M'))['Sales'].sum().reset_index()
        monthly_sales['Order Date'] = monthly_sales['Order Date'].astype(str)

        fig1 = px.line(monthly_sales, x='Order Date', y='Sales',
                       title='Monthly Sales Trend',
                       labels={'Order Date': 'Month', 'Sales': 'Sales ($)'})
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Sales by category
        category_sales = filtered_df.groupby('Category')['Sales'].sum().reset_index()
        fig2 = px.pie(category_sales, values='Sales', names='Category',
                      title='Sales Distribution by Category')
        st.plotly_chart(fig2, use_container_width=True)

    # Regional Analysis
    st.header("🗺️ Regional Performance")
    col1, col2 = st.columns(2)

    with col1:
        region_sales = filtered_df.groupby('Region')['Sales'].sum().reset_index()
        fig3 = px.bar(region_sales, x='Region', y='Sales',
                      title='Sales by Region',
                      color='Sales', color_continuous_scale='Viridis')
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        region_profit = filtered_df.groupby('Region')['Profit'].sum().reset_index()
        fig4 = px.bar(region_profit, x='Region', y='Profit',
                      title='Profit by Region',
                      color='Profit', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig4, use_container_width=True)

    # 7-Day Forecast
    if forecast is not None:
        st.header("🔮 7-Day Sales Forecast")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Forecast Period", f"{forecast['Date'].min().strftime('%Y-%m-%d')} to {forecast['Date'].max().strftime('%Y-%m-%d')}")
        with col2:
            total_forecast = forecast['Forecasted_Sales'].sum()
            st.metric("Total Forecasted Sales", f"${total_forecast:,.0f}")
        with col3:
            avg_daily = forecast['Forecasted_Sales'].mean()
            st.metric("Average Daily Sales", f"${avg_daily:,.0f}")

        # Forecast chart
        fig5 = go.Figure()

        # Add historical data (last 30 days)
        historical_recent = filtered_df.groupby('Order Date')['Sales'].sum().reset_index()
        historical_recent = historical_recent.tail(30)

        fig5.add_trace(go.Scatter(
            x=historical_recent['Order Date'],
            y=historical_recent['Sales'],
            mode='lines+markers',
            name='Historical Sales',
            line=dict(color='#2E86AB', width=2)
        ))

        # Add forecast
        fig5.add_trace(go.Scatter(
            x=forecast['Date'],
            y=forecast['Forecasted_Sales'],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#A23B72', width=2, dash='dash')
        ))

        # Add confidence interval
        fig5.add_trace(go.Scatter(
            x=pd.concat([forecast['Date'], forecast['Date'][::-1]]),
            y=pd.concat([forecast['Upper_Bound'], forecast['Lower_Bound'][::-1]]),
            fill='toself',
            fillcolor='rgba(162, 59, 114, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Confidence Interval'
        ))

        fig5.update_layout(
            title='7-Day Sales Forecast with Confidence Intervals',
            xaxis_title='Date',
            yaxis_title='Sales ($)',
            hovermode='x unified'
        )

        st.plotly_chart(fig5, use_container_width=True)

        # Forecast table
        st.subheader("📋 Detailed Forecast")
        forecast_display = forecast.copy()
        forecast_display['Date'] = forecast_display['Date'].dt.strftime('%Y-%m-%d')
        forecast_display['Forecasted_Sales'] = forecast_display['Forecasted_Sales'].apply(lambda x: f"${x:,.2f}")
        forecast_display['Lower_Bound'] = forecast_display['Lower_Bound'].apply(lambda x: f"${x:,.2f}")
        forecast_display['Upper_Bound'] = forecast_display['Upper_Bound'].apply(lambda x: f"${x:,.2f}")

        st.dataframe(forecast_display, use_container_width=True)

        # Download forecast
        st.markdown("---")
        st.subheader("📥 Download Forecast")

        csv = forecast.to_csv(index=False)
        st.download_button(
            label="Download 7-Day Forecast as CSV",
            data=csv,
            file_name="sales_forecast_7days.csv",
            mime="text/csv"
        )
    else:
        st.header("🔮 7-Day Sales Forecast")
        st.info("Forecast data not available. Please run the forecasting notebook to generate predictions.")

    # Business Insights
    st.header("💡 Business Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📌 Key Findings")
        st.markdown("""
        - **Sales Decline:** 15.2% decrease over 4 years
        - **Best Region:** West region with 32.4% sales share
        - **Most Profitable:** Technology category (18.2% margin)
        - **Peak Season:** November-December (25% higher sales)
        """)

    with col2:
        st.subheader("🎯 Recommendations")
        st.markdown("""
        - **Inventory:** Increase stock by 15% for peak days
        - **Marketing:** Focus on South region (fastest growing)
        - **Discounts:** Cap at 20% to protect margins
        - **Forecast:** Use XGBoost model for planning
        """)

except FileNotFoundError as e:
    st.error(f"Error loading data: {e}")
    st.info("Please run the notebooks first to generate the required data files.")