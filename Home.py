import streamlit as st
import pandas as pd

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")


html ="""
    <div style="text-align: center; color: white; font-size: 30px; font-weight: bold;">
        Shopping Cart EDA Project
    </div>
    """


st.image("canva-pink-and-white-minimalist-e-commerce-presentation-pUrMakjsI6U.jpg")

st.markdown(html, unsafe_allow_html= True)

# Load the data
df = pd.read_parquet('cleaned_data.parquet')

# Show sample of data
st.subheader("Data Overview")
st.dataframe(df)

# Data description table for all columns (what each column represents)
st.subheader("Data Description")

import streamlit as st
import pandas as pd

# Load the dataset
df = pd.read_csv("cleaned_data.csv")

# Define descriptions for the columns in your dataset
descriptions = {
    'customer_name': 'Name of the customer',
    'gender': 'Gender of the customer',
    'age': 'Age of the customer in years',
    'city': 'City where the order was placed or delivered',
    'state': 'State where the order was placed or delivered',
    'order_date': 'Date when the order was placed',
    'delivery_date': 'Date when the order was successfully delivered',
    'price_per_unit': 'Price for a single unit of the product',
    'quantity': 'Number of units purchased in the order',
    'total_price': 'Total cost for the ordered quantity (price_per_unit * quantity)',
    'product_type': 'Category or type of the product',
    'product_name': 'Name of the purchased product',
    'size': 'Size of the product',
    'colour': 'Color of the product',
    'stock': 'Available stock count for the product',
    'order_month_name': 'Name of the month the order was placed',
    'order_day': 'Day of the month the order was placed',
    'order_weekday_name': 'Day of the week the order was placed',
    'delivery_days': 'Total number of days taken to deliver the order',
    'month': 'Numeric representation of the order month'
}

# Filter out ID columns (e.g., customer_id, order_id, sales_id, product_id)
# This checks if the column name ends with '_id' or is exactly 'id'
filtered_columns = [col for col in df.columns if not col.lower().endswith('id')]

# Create a list of dictionaries for the table
table_data = []
for col in filtered_columns:
    desc = descriptions.get(col, "No description available")
    table_data.append({
        "Column Name": col, 
        "Description": desc
    })

# Convert to a DataFrame for clean formatting in Streamlit
description_df = pd.DataFrame(table_data)

# Display the table in the Streamlit app
st.subheader("Data Dictionary")
st.table(description_df) 
# Note: You can also use st.dataframe(description_df, use_container_width=True) if you want it to be sortable