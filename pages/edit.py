import streamlit as st, datetime
from common import table_selector, TABLES, none_if_blank, update_row, fetch_all

table = table_selector()
META = TABLES[table]
PK, COLS, REQ = META["pk"], META["cols"], set(META["required"])

st.title(f"✏️ Edit → {table}")

rows = fetch_all(table)
if not rows:
    st.info("No data yet.")
    st.stop()

selected = st.selectbox("Select row", rows, format_func=lambda r: f"{table[:-1]} {r[PK]}")
pk_val   = selected[PK]

with st.form(f"edit_{pk_val}"):
    inputs = {}
    for col in COLS:
        cur = selected.get(col)
        kw  = dict(value=cur or "")
        if col in (
            "main_content","markdown_sections","code_example","external_links",
            "table_data","reference_links","assignment_details","solution",
            "extra_html","prompt","question","options_json"
        ):
            kw["height"] = 120 if col=="main_content" else 90
            inputs[col]  = st.text_area(col, **kw)
        elif col == "task_type":
            inputs[col] = st.selectbox(col, ("quiz","assignment"), index=0 if cur=="quiz" else 1)
        elif col in ("points","display_order"):
            inputs[col] = st.number_input(col, min_value=1, value=int(cur or 1), step=1)
        elif col == "due_date":
            init = cur if isinstance(cur, datetime.date) else datetime.date.today()
            inputs[col] = st.date_input(col, value=init)
        else:
            inputs[col] = st.text_input(col, **kw)

    if st.form_submit_button("Update"):
        if not all(inputs[c] for c in REQ):
            st.error(f"Required fields: {', '.join(REQ)}")
        else:
            vals = tuple(none_if_blank(inputs[c]) for c in COLS)
            update_row(table, pk_val, vals)
            st.success("✅ Row updated.")
