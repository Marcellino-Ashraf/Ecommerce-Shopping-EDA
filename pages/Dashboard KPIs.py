import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Marketing Report", page_icon="📈", layout="wide")


html ="""
    <div style="text-align: center; color: white; font-size: 30px; font-weight: bold;">
        Shopping Cart EDA Project
    </div>
    """

st.markdown(html, unsafe_allow_html= True)

# Load the data
df = pd.read_parquet('cleaned_data.parquet')

# Total number of customers
total_customers = round(df['customer_id'].nunique(), 2)

# Total number of orders
total_orders = round(df['order_id'].nunique(), 2)

# Total revenue
total_revenue = round(df['total_price'].sum(), 2)

# Average order value
average_order_value = round(df.groupby('order_id')['total_price'].sum().mean(), 2)

# Display KPIs in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Customers", total_customers)

with col2:
    st.metric("Total Orders", total_orders)

with col3:
    st.metric("Total Revenue", total_revenue)

with col4:
    st.metric("Average Order Value", average_order_value)

# Total Revenue Daily
df_sorted = df.sort_values(by='order_date')
revenue_by_day = df_sorted.groupby('order_date')['total_price'].sum().reset_index()
plot_daily_revenue = px.line(revenue_by_day, x='order_date', y='total_price', title='Total Revenue Daily', labels={'order_date': 'Order Date', 'total_price': 'Total Revenue'})

st.plotly_chart(plot_daily_revenue)

# Total Revenue Monthly
plot_df = df_sorted.groupby('month')['total_price'].sum().reset_index()
plot_monthly_revenue = px.line(data_frame=plot_df, x='month', y='total_price', markers=True, text = 'total_price',
                        labels= {'month' : 'Month', 'total_price' : 'Monthly Revenue'},
                        title= 'Monthly Revenue Over Time').update_traces(textposition='top center')

st.plotly_chart(plot_monthly_revenue)


# Products Pie Charts
col_1, col_2 = st.columns(2)

with col_1:
    st.plotly_chart(px.pie(data_frame= df, names= 'product_type', hole= 0.5))

with col_2:
    st.plotly_chart(px.pie(data_frame= df, names= 'size', hole= 0.5))