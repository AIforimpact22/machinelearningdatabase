import streamlit as st, datetime
from common import table_selector, TABLES, none_if_blank, update_row, fetch_all, delete_row
from collections import defaultdict
import json

table = table_selector()
META = TABLES[table]
PK, COLS, REQ = META["pk"], META["cols"], set(META["required"])

st.title(f"✏️ Edit → {table}")

rows = fetch_all(table)
if not rows:
    st.info("No data yet.")
    st.stop()

# Group by module and sort by tab_number
modules = defaultdict(list)
for row in rows:
    modules[row["module"]].append(row)
for module, module_rows in modules.items():
    modules[module] = sorted(module_rows, key=lambda r: r.get("tab_number", 0))

col1, col2 = st.columns([1.2, 2])

with col1:
    st.header("Modules & Tabs")
    if "edit_selected_pk" not in st.session_state:
        st.session_state.edit_selected_pk = None
    for module in sorted(modules.keys()):
        with st.expander(f"Module: {module}", expanded=True):
            for row in modules[module]:
                label = f"{table[:-1].capitalize()} {row[PK]} (Tab {row.get('tab_number', '-')})"
                if st.button(label, key=f"edit_{module}_{row[PK]}"):
                    st.session_state.edit_selected_pk = row[PK]

with col2:
    st.header("Edit Row")
    selected = None
    if st.session_state.edit_selected_pk is not None:
        for row in rows:
            if row[PK] == st.session_state.edit_selected_pk:
                selected = row
                break
    if selected:
        pk_val = selected[PK]
        with st.form(f"edit_{pk_val}"):
            inputs = {}
            for col in COLS:
                cur = selected.get(col)
                kw = dict(value=cur or "")
                if col in (
                    "main_content", "markdown_sections", "code_example", "external_links",
                    "table_data", "reference_links", "assignment_details", "solution",
                    "extra_html", "prompt", "question", "options_json"
                ):
                    kw["height"] = 120 if col == "main_content" else 90
                    inputs[col] = st.text_area(col, **kw)
                elif col == "task_type":
                    inputs[col] = st.selectbox(col, ("quiz", "assignment"), index=0 if cur == "quiz" else 1)
                elif col in ("points", "display_order"):
                    inputs[col] = st.number_input(col, min_value=1, value=int(cur or 1), step=1)
                elif col == "due_date":
                    init = cur if isinstance(cur, datetime.date) else datetime.date.today()
                    inputs[col] = st.date_input(col, value=init)
                else:
                    inputs[col] = st.text_input(col, **kw)

            colu1, colu2 = st.columns([2, 1])
            update_clicked = colu1.form_submit_button("Update")
            delete_clicked = colu2.form_submit_button("Delete", type="primary")

            if update_clicked:
                if not all(inputs[c] for c in REQ):
                    st.error(f"Required fields: {', '.join(REQ)}")
                else:
                    vals = tuple(none_if_blank(inputs[c]) for c in COLS)
                    update_row(table, pk_val, vals)
                    st.success("✅ Row updated.")

            # Delete logic with confirmation
            if delete_clicked:
                st.warning("⚠️ This will permanently delete this row!")
                confirm = st.checkbox("Yes, I want to delete this row", key=f"delete_confirm_{pk_val}")
                if confirm:
                    delete_row(table, pk_val)
                    st.success("✅ Row deleted.")
                    # Reset selection after delete
                    st.session_state.edit_selected_pk = None
                    st.experimental_rerun()
    else:
        st.info("Select a row from the left to edit or delete its details.")
