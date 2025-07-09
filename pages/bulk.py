# pages/bulk.py

import streamlit as st
import pandas as pd
import io

from common import table_selector, TABLES, insert_row, update_row

# ────────────────── 1. Pick table & metadata ──────────────────
table    = table_selector()
META     = TABLES[table]
PK       = META["pk"]
COLS     = META["cols"]
REQUIRED = set(META["required"])

st.title(f"📥 Bulk CSV → {table}")

# ────────────────── 2. Show CSV template ───────────────────────
st.markdown("#### CSV template")
sample_df = pd.DataFrame(META["sample"])
buf = io.StringIO()
sample_df.to_csv(buf, index=False)
st.code(buf.getvalue(), language="csv")
st.download_button("Download template CSV", buf.getvalue(),
                   file_name=f"{table}_sample.csv")

# ────────────────── 3. Upload your CSV ─────────────────────────
uploaded = st.file_uploader("Upload your CSV here", type="csv")
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded)
st.markdown("##### Preview of uploaded data")
st.dataframe(df.head(), use_container_width=True)

# ────────────────── 4. Check for required columns ──────────────
missing_cols = [c for c in REQUIRED if c not in df.columns]
if missing_cols:
    st.error(f"Missing required columns in CSV: {', '.join(missing_cols)}")
    st.stop()

# ────────────────── 5. Ensure all expected columns exist ───────
for c in COLS:
    if c not in df.columns:
        df[c] = None

# ────────────────── 6. Coerce integer columns ─────────────────
for intcol in ("display_order", "points"):
    if intcol in df.columns:
        df[intcol] = (
            pd.to_numeric(df[intcol], errors="coerce")
              .fillna(1)
              .astype(int)
        )

mode = st.radio("Mode", ("Insert only", "Update if PK present"))

# ────────────────── 7. Import loop ────────────────────────────
if st.button("Import CSV"):
    inserted = updated = skipped = 0

    for idx, row in df.iterrows():
        # — build clean values list —
        vals = []
        bad_required = False

        for col in COLS:
            raw = row[col]

            # treat any pandas NA or blank string as None
            if pd.isna(raw) or (isinstance(raw, str) and raw.strip() == ""):
                val = None
            else:
                val = raw

            # check required
            if col in REQUIRED and val is None:
                bad_required = True

            vals.append(val)

        if bad_required:
            skipped += 1
            st.warning(f"Row {idx}: missing required field → skipped")
            continue

        # — detect user-supplied PK for update only —
        pk_val = None
        if PK in df.columns and pd.notna(row[PK]):
            try:
                pk_val = int(row[PK])
            except:
                pk_val = None

        # — execute INSERT or UPDATE —
        try:
            if mode == "Update if PK present" and pk_val:
                update_row(table, pk_val, tuple(vals))
                updated += 1
            else:
                insert_row(table, tuple(vals))
                inserted += 1
        except Exception as e:
            skipped += 1
            st.error(f"Row {idx}: {e}")

    st.success(f"Done! Inserted: {inserted} | Updated: {updated} | Skipped: {skipped}")
