import streamlit as st, datetime
import json
from common import table_selector, TABLES, none_if_blank, insert_row, fetch_all

table = table_selector()
META = TABLES[table]
PK, COLS, REQ = META["pk"], META["cols"], set(META["required"])

st.title(f"➕ Add → {table}")

with st.form("add_form", clear_on_submit=True):
    inputs = {}
    for col in COLS:
        if col in (
            "main_content","markdown_sections","code_example","external_links",
            "table_data","reference_links","assignment_details","solution",
            "extra_html","prompt","question","options_json"
        ):
            inputs[col] = st.text_area(col, height=120 if col=="main_content" else 90)
        elif col == "task_type":
            inputs[col] = st.selectbox(col, ("quiz","assignment"))
        elif col in ("points","display_order"):
            inputs[col] = st.number_input(col, min_value=1, value=1, step=1)
        elif col == "due_date":
            inputs[col] = st.date_input(col, value=datetime.date.today())
        else:
            inputs[col] = st.text_input(col)

    if st.form_submit_button("Save"):
        if not all(inputs[c] for c in REQ):
            st.error(f"Required fields: {', '.join(REQ)}")
        else:
            vals = tuple(none_if_blank(inputs[c]) for c in COLS)
            insert_row(table, vals)
            st.success("✅ Row inserted.")

st.divider()
st.dataframe(fetch_all(table), use_container_width=True)
