import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Univariate Analysis", page_icon="📊", layout="wide")


html ="""
    <div style="text-align: center; color: white; font-size: 30px; font-weight: bold;">
        Shopping Cart EDA Project
    </div>
    """


st.image("canva-pink-and-white-minimalist-e-commerce-presentation-pUrMakjsI6U.jpg")

st.markdown(html, unsafe_allow_html= True)

df = pd.read_parquet('cleaned_data.parquet')

# Make two tabs for numerical and categorical analysis
tab1, tab2 = st.tabs(["Numerical Analysis", "Categorical Analysis"])

with tab1:
    st.subheader("Numerical Analysis")

    num_cols = df.select_dtypes(include = 'number').columns.drop(['customer_id', 'order_id', 'product_id', 'sales_id'])
    col_select = st.selectbox("Select a numerical column for analysis", num_cols, key="num_col_select")

    chart_select = st.radio("Select chart type", ["Histogram", "Box Plot"], key="num_chart_select")

    fig = px.histogram(df, x=col_select, title=f"Distribution of {col_select}") if chart_select == "Histogram" else px.box(df, y=col_select, title=f"Box Plot of {col_select}")

    if st.button("Generate Chart", key="num_generate_chart"):
        st.plotly_chart(fig, use_container_width=True)

#categorical analysis
with tab2:
    st.subheader("Categorical Analysis")

    cat_cols = df.select_dtypes(include = 'object').columns.drop('customer_name')
    cat_col_select = st.selectbox("Select a categorical column for analysis", cat_cols, key="cat_col_select")

    cat_chart_select = st.radio("Select chart type", ["Histogram", "Bar Chart", "Pie Chart"], key="cat_chart_select")

    fig = px.histogram(df, x=cat_col_select, title=f"Distribution of {cat_col_select}", text_auto=True).update_xaxes(categoryorder="max descending") if cat_chart_select == "Histogram" else (px.bar(df[cat_col_select].value_counts().reset_index(), x=cat_col_select, y=cat_col_select, title=f"Bar Chart of {cat_col_select}") if cat_chart_select == "Bar Chart" else px.pie(df, names=cat_col_select, title=f"Pie Chart of {cat_col_select}"))

    if st.button("Generate Chart", key="cat_generate_chart"):
        st.plotly_chart(fig, use_container_width=True)
