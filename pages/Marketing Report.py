import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Marketing Report", page_icon="📈", layout="wide")


html ="""
    <div style="text-align: center; color: white; font-size: 30px; font-weight: bold;">
        Shopping Cart EDA Project
    </div>
    """


st.image("canva-pink-and-white-minimalist-e-commerce-presentation-pUrMakjsI6U.jpg")

st.markdown(html, unsafe_allow_html= True)

df = pd.read_parquet('cleaned_data.parquet')


state = st.sidebar.multiselect("Select a State", options=['All States'] + df['state'].unique().tolist(), key='state_select', default=['All States'])

# filter the df for state
if 'All States' not in state:
    df = df[df['state'].isin(state)]

# The user can choose a start date and an end date for the data they want to see. The default values are the minimum and maximum dates in the dataset.
min_date = df['order_date'].min()
max_date = df['order_date'].max()

start_date = st.sidebar.date_input("Start Date", value=min_date)
end_date = st.sidebar.date_input("End Date", value=max_date)

# filter the df for dates
# Convert the Python date objects to pandas Timestamps to compare with the dataframe column
start_timestamp = pd.to_datetime(start_date)
end_timestamp = pd.to_datetime(end_date)

df = df[(df['order_date'] >= start_timestamp) & (df['order_date'] <= end_timestamp)]

st.dataframe(df)

# Number of orders per state
orders_per_state = df.groupby('state')['order_id'].nunique().sort_values(ascending=True).reset_index()

st.plotly_chart(px.bar(orders_per_state, x='order_id', y='state', title='Number of Orders per State', labels={'state': 'State', 'order_id': 'Number of Orders'}, text_auto='.2s').update_traces(textposition='outside'))

# Count of orders per product per state
Number_of_shown_products = st.sidebar.slider("Number of Products to Show", min_value=2, max_value=df['product_name'].nunique(), value=5, step=1)
orders_per_product_state = df.groupby(['product_name'])['order_id'].nunique().reset_index().sort_values(by='order_id', ascending=False).head(Number_of_shown_products)
st.plotly_chart(px.bar(orders_per_product_state, x='order_id', y='product_name', title='Number of Orders per Product per State', labels={'product_name': 'Product', 'order_id': 'Number of Orders'}, text_auto='.2s').update_traces(textposition='outside'))
