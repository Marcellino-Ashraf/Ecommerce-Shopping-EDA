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