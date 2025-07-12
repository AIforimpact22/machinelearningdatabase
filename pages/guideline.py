import streamlit as st, json
from common import table_selector, fetch_all, TABLES
from collections import defaultdict

table = table_selector()
META = TABLES[table]
PK = META["pk"]

st.title(f"📄 Guideline → {table}")

rows = fetch_all(table)
if not rows:
    st.info("No data to show.")
    st.stop()

# Group rows by module and sort by tab_number
modules = defaultdict(list)
for row in rows:
    modules[row["module"]].append(row)
for module, module_rows in modules.items():
    modules[module] = sorted(module_rows, key=lambda r: r.get("tab_number", 0))

# --- UI Layout ---
col1, col2 = st.columns([1.2, 2])

with col1:
    st.header("Modules & Tabs")
    # A session state to track which row is selected
    if "selected_pk" not in st.session_state:
        st.session_state.selected_pk = None

    for module in sorted(modules.keys()):
        with st.expander(f"Module: {module}", expanded=True):
            for row in modules[module]:
                label = f"{table[:-1].capitalize()} {row[PK]} (Tab {row.get('tab_number', '-')})"
                if st.button(label, key=f"{module}_{row[PK]}"):
                    st.session_state.selected_pk = row[PK]

with col2:
    st.header("Selected Row")
    # Find selected row from session state
    selected = None
    if st.session_state.selected_pk is not None:
        for row in rows:
            if row[PK] == st.session_state.selected_pk:
                selected = row
                break
    if selected:
        st.code(json.dumps(selected, indent=2, default=str), language="json")
    else:
        st.info("Select any row from the left to see its details.")

