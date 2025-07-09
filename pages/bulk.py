import streamlit as st, io, pandas as pd
from common import table_selector, TABLES, none_if_blank, insert_row, update_row

table = table_selector()
META = TABLES[table]
PK, COLS = META["pk"], META["cols"]

st.title(f"📥 Bulk CSV → {table}")

st.markdown("#### CSV template")
sample_df = pd.DataFrame(META["sample"])
buf = io.StringIO()
sample_df.to_csv(buf, index=False)
st.code(buf.getvalue(), language="csv")
st.download_button("Download sample CSV", buf.getvalue(), f"{table}_sample.csv")

file = st.file_uploader("Upload your CSV", type="csv")
if not file:
    st.stop()

df = pd.read_csv(file)
st.markdown("Preview:")
st.dataframe(df.head())

for col in COLS:                 # add missing cols as blank
    if col not in df.columns:
        df[col] = None

mode = st.radio("Mode", ("Insert only", "Update if PK present"))

if st.button("Import"):
    ins = upd = 0
    for idx, row in df.iterrows():
        vals = []
        for col in COLS:
            val = row.get(col)
            if col in ("display_order","points"):
                val = int(val) if pd.notna(val) else 1
            vals.append(none_if_blank(val))
        vals = tuple(vals)

        pk_val = int(row[PK]) if PK in df.columns and pd.notna(row[PK]) else None
        try:
            if mode == "Update if PK present" and pk_val:
                update_row(table, pk_val, vals)
                upd += 1
            else:
                insert_row(table, vals)
                ins += 1
        except Exception as e:
            st.error(f"Row {idx}: {e}")

    st.success(f"Inserted: {ins} | Updated: {upd}")
