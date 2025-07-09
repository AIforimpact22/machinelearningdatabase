# pages/bulk.py
import streamlit as st, pandas as pd, io
from common import table_selector, TABLES, none_if_blank, insert_row, update_row

# ───────────────────── 1. Which table? ──────────────────────
table = table_selector()
META  = TABLES[table]
PK, COLS, REQ = META["pk"], META["cols"], set(META["required"])

st.title(f"📥 Bulk CSV → {table}")

# ───────────────────── 2. Show template CSV ─────────────────
sample_df = pd.DataFrame(META["sample"])
buf = io.StringIO()
sample_df.to_csv(buf, index=False)
st.markdown("#### CSV template")
st.code(buf.getvalue(), language="csv")
st.download_button("Download template", buf.getvalue(),
                   file_name=f"{table}_sample.csv")

# ───────────────────── 3. Upload file ───────────────────────
file = st.file_uploader("Upload your CSV", type="csv")
if file is None:
    st.stop()

df = pd.read_csv(file)
st.markdown("Preview:")
st.dataframe(df.head(), use_container_width=True)

# ───────────────────── 4. Validate columns ──────────────────
missing_req = [c for c in REQ if c not in df.columns]
if missing_req:
    st.error(f"CSV is missing **required** columns: {', '.join(missing_req)}")
    st.stop()

# Add any optional columns that are absent so we can iterate safely
for col in COLS:
    if col not in df.columns:
        df[col] = None

# ───────────────────── 5. Normalise types ───────────────────
for col in ("display_order", "points"):
    if col in df.columns:
        df[col] = (
            pd.to_numeric(df[col], errors="coerce")
              .fillna(1)
              .astype(int)
        )

mode = st.radio("Mode", ("Insert only", "Update if PK present"))

# ───────────────────── 6. Import rows ───────────────────────
if st.button("Import"):
    ins = upd = skip = 0

    for idx, row in df.iterrows():

        # (a) Drop rows that still lack any required cell value
        if any(pd.isna(row[c]) or str(row[c]).strip() == "" for c in REQ):
            skip += 1
            st.warning(f"Row {idx}: missing required data → skipped")
            continue

        # (b) Tuple of values in the exact order COLS expects
        vals = tuple(none_if_blank(row.get(c)) for c in COLS)

        # (c) Do we have a PK for update?
        pk_val = (
            int(row[PK]) if PK in df.columns and pd.notna(row[PK]) else None
        )

        try:
            if mode == "Update if PK present" and pk_val:
                update_row(table, pk_val, vals)
                upd += 1
            else:
                insert_row(table, vals)
                ins += 1
        except Exception as e:
            skip += 1
            st.error(f"Row {idx}: {e}")

    st.success(f"Finished →  Inserted: {ins}   Updated: {upd}   Skipped: {skip}")
