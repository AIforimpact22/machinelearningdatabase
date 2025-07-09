import streamlit as st
from common import table_selector, fetch_all, TABLES

st.set_page_config(page_title="Course‑Manager Home", layout="wide")

table = table_selector()

st.title("📚 Course Manager — Home")
st.markdown(
    """
    Use the left‑hand navigation to **Add**, **Edit**, **Bulk upload** or **view Guidelines**  
    for each table. This home page just gives you a quick overview.
    """
)

data = fetch_all(table)
if data:
    st.dataframe(data, use_container_width=True)
else:
    st.info(f"No rows yet in **{table}**")
