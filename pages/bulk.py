# pages/bulk.py
import streamlit as st, pandas as pd, io
from common import TABLES, none_if_blank, insert_row, update_row

# ───────────────────── 1. Helper ────────────────────────────
def choose_table_for_csv(df: pd.DataFrame) -> str | None:
    """
    Return the table whose required-columns are fully satisfied
    by this dataframe.  If none or several match, return None.
    """
    candidates = []
    for name, meta in TABLES.items():
        if set(meta["required"]).issubset(df.columns):
            candidates.append(name)
    return candidates[0] if len(candidates) == 1 else None


# ───────────────────── 2. Upload area ───────────────────────
st.title("📥 Bulk CSV import")

file = st.file_uploader("Upload your CSV", type="csv")
if file is None:
    st.stop()

df = pd.read_csv(file)
st.markdown("Preview:")
st.dataframe(df.head(), use_container_width=True)

# ───────────────────── 3. Work out the table ────────────────
if "table_choice" not in st.session_state:
    st.session_state.table_choice = list(TABLES.keys())[0]

selected_table = st.session_state.table_choice

auto_table = choose_table_for_csv(df)
if auto_table and auto_table != selected_table:
    st.info(
        f"⚡ Detected that your CSV fits **{auto_table}** "
        f"(not **{selected_table}**). Switching automatically…"
    )
    st.session_state.table_choice = auto_table
    st.experimental_rerun()

table = selected_table            # after possible rerun
META  = TABLES[table]
PK, COLS, REQ = META["pk"], META["cols"], set(META["required"])

st.subheader(f"Target table → `{table}`")

# ───────────────────── 4. Check required columns ────────────
missing_req = [c for c in REQ if c not in df.columns]
if missing_req:
    st.error(
        "CSV is missing **required** columns: "
        + ", ".join(missing_req)
    )
    st.stop()

# Add any optional columns that are absent so we can iterate safely
for col in COLS:
    if col not in df.columns:
        df[col] = None

# ───────────────────── 5. Normalise integer columns ─────────
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

        # (a) Skip rows that still lack any required cell value
        if any(pd.isna(row[c]) or str(row[c]).strip() == "" for c in REQ):
            skip += 1
            st.warning(f"Row {idx}: missing required data → skipped")
            continue

        # (b) Build the value list in the exact order COLS expects
        vals = tuple(none_if_blank(row.get(c)) for c in COLS)

        # (c) Check for primary key value only if the CSV supplies it
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

    st.success(
        f"Finished →  Inserted: {ins}   Updated: {upd}   Skipped: {skip}"
    )
