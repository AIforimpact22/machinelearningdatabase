# pages/bulk.py

import streamlit as st
import pandas as pd
import io

from common import table_selector, TABLES, none_if_blank, insert_row, update_row

# ───────────────────── 1. Which table? ──────────────────────
table   = table_selector()
META    = TABLES[table]
PK      = META["pk"]
COLS    = META["cols"]
REQUIRED = set(META["required"])

st.title(f"📥 Bulk CSV → {table}")

# ───────────────────── 2. CSV template ──────────────────────
st.markdown("#### CSV template")
sample_df = pd.DataFrame(META["sample"])
buf = io.StringIO()
sample_df.to_csv(buf, index=False)
st.code(buf.getvalue(), language="csv")
st.download_button("Download template", buf.getvalue(),
                   file_name=f"{table}_sample.csv")

# ───────────────────── 3. Upload your CSV ───────────────────
uploaded = st.file_uploader("Upload your CSV here", type="csv")
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded)
st.markdown("##### Preview of uploaded data")
st.dataframe(df.head(), use_container_width=True)

# ───────────────────── 4. Table-match check ─────────────────
# Find which tables this CSV could belong to
matches = [
    name
    for name, meta in TABLES.items()
    if set(meta["required"]).issubset(df.columns)
]

if table not in matches:
    if len(matches) == 1:
        st.error(
            f"⚠️  It looks like your CSV fits **{matches[0]}**, "
            f"but you have **{table}** selected.  \n"
            "Please switch tables in the sidebar and try again."
        )
    elif matches:
        st.error(
            f"⚠️  Your CSV matches multiple tables ({', '.join(matches)}).  \n"
            "Please pick the correct one in the sidebar."
        )
    else:
        missing = REQUIRED - set(df.columns)
        st.error(
            f"⚠️  CSV is missing required columns for **{table}**: "
            f"{', '.join(missing)}"
        )
    st.stop()

# ───────────────────── 5. Prepare DataFrame ─────────────────
# Ensure all expected columns exist so we can iterate safely
for col in COLS:
    if col not in df.columns:
        df[col] = None

# Coerce integer columns so they never land as NULL
for intcol in ("display_order", "points"):
    if intcol in df.columns:
        df[intcol] = (
            pd.to_numeric(df[intcol], errors="coerce")
              .fillna(1)
              .astype(int)
        )

mode = st.radio("Mode", ("Insert only", "Update if PK present"))

# ───────────────────── 6. Do the import ────────────────────
if st.button("Import CSV"):
    inserted = updated = skipped = 0

    for idx, row in df.iterrows():
        # skip if any required cell is blank/null
        if any(pd.isna(row[c]) or str(row[c]).strip() == "" for c in REQUIRED):
            skipped += 1
            st.warning(f"Row {idx}: missing required data → skipped")
            continue

        # build tuple in the exact order COLS defines (no PK here!)
        values = tuple(none_if_blank(row.get(c)) for c in COLS)

        # only attempt update if user-supplied a PK in the CSV
        pk_val = None
        if PK in df.columns and pd.notna(row[PK]):
            try:
                pk_val = int(row[PK])
            except:
                pass

        try:
            if mode == "Update if PK present" and pk_val:
                update_row(table, pk_val, values)
                updated += 1
            else:
                insert_row(table, values)
                inserted += 1
        except Exception as e:
            skipped += 1
            st.error(f"Row {idx}: {e}")

    st.success(
        f"✅ Done!  Inserted: {inserted}   Updated: {updated}   Skipped: {skipped}"
    )
