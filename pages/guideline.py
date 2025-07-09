import streamlit as st, json
from common import table_selector, fetch_all, TABLES

table   = table_selector()
META    = TABLES[table]
PK      = META["pk"]

st.title(f"📄 Guideline → {table}")

rows = fetch_all(table)
if not rows:
    st.info("No data to show.")
    st.stop()

selected = st.selectbox("Select row", rows,
                        format_func=lambda r: f"{table[:-1]} {r[PK]}")
st.code(json.dumps(selected, indent=2, default=str), language="json")
