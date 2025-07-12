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

# Group by 'module'
modules = defaultdict(list)
for row in rows:
    modules[row["module"]].append(row)

# Sort rows within each module by 'tab_number'
for module, module_rows in modules.items():
    modules[module] = sorted(module_rows, key=lambda r: r.get("tab_number", 0))

selected = None
for module in sorted(modules.keys()):
    with st.expander(f"Module: {module}", expanded=True):
        # Show each row as a button, display PK and tab_number for clarity
        for row in modules[module]:
            label = f"{table[:-1].capitalize()} {row[PK]} (Tab {row.get('tab_number', '-')})"
            if st.button(label, key=f"{module}_{row[PK]}"):
                selected = row

if selected:
    st.subheader("Selected Row")
    st.code(json.dumps(selected, indent=2, default=str), language="json")
elif len(rows) > 0:
    st.info("Click any row above to see its details.")
