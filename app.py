# app_course_tabs.py  — Add • Edit • Guideline • Bulk Upload
import streamlit as st
import mysql.connector
import pandas as pd
import json
from typing import Any, Dict, List, Tuple

# ───────────────────── 1. MySQL connection ─────────────────────
@st.cache_resource
def get_conn():
    cfg = st.secrets["mysql"]
    return mysql.connector.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        autocommit=True,
    )

conn = get_conn()

# ───────────────────── 2. Ensure table ─────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS course_tabs (
  tab_id INT AUTO_INCREMENT PRIMARY KEY,
  module VARCHAR(50) NOT NULL,
  tab_number VARCHAR(10) NOT NULL,
  title VARCHAR(255) NOT NULL,
  subtitle VARCHAR(255),
  video_url VARCHAR(500),
  video_upload VARCHAR(500),
  main_content TEXT,
  markdown_sections TEXT,
  code_example TEXT,
  external_links TEXT,
  table_data TEXT,
  reference_links TEXT,
  custom_module VARCHAR(255),
  display_order INT NOT NULL,
  extra_html TEXT,
  prompt TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""
with conn.cursor(buffered=True) as cur:
    cur.execute(DDL)

# ───────────────────── 3. Helpers ──────────────────────────────
COLS = [
    "module", "tab_number", "title", "subtitle", "video_url", "video_upload",
    "main_content", "markdown_sections", "code_example", "external_links",
    "table_data", "reference_links", "custom_module", "display_order",
    "extra_html", "prompt"
]

def none_if_blank(v: str | None) -> Any:
    return None if (v is None or str(v).strip() == "") else v

def insert_tab(row: Tuple):
    with conn.cursor(buffered=True) as cur:
        cur.execute(
            f"""
            INSERT INTO course_tabs ({', '.join(COLS)})
            VALUES ({', '.join(['%s'] * len(COLS))})
            """,
            row,
        )

def update_tab(tab_id: int, row: Tuple):
    with conn.cursor(buffered=True) as cur:
        assignments = ", ".join(f"{col}=%s" for col in COLS)
        cur.execute(
            f"UPDATE course_tabs SET {assignments} WHERE tab_id=%s",
            row + (tab_id,),
        )

def fetch_tabs() -> List[Dict]:
    with conn.cursor(buffered=True, dictionary=True) as cur:
        cur.execute(
            "SELECT * FROM course_tabs ORDER BY module, display_order, tab_number"
        )
        return cur.fetchall()

# ───────────────────── 4. Page selector ────────────────────────
page = st.sidebar.radio("Page", ("Add", "Edit", "Bulk Upload", "Guideline"))

# ───────────────────── 5. Add page ─────────────────────────────
def add_page():
    st.title("Add New Row")

    with st.form("add_row", clear_on_submit=True):
        inputs = {}
        inputs["module"]            = st.text_input("**module**")
        inputs["tab_number"]        = st.text_input("**tab_number**")
        inputs["title"]             = st.text_input("**title**")
        inputs["subtitle"]          = st.text_input("subtitle")
        inputs["video_url"]         = st.text_input("video_url")
        inputs["video_upload"]      = st.text_input("video_upload")
        inputs["main_content"]      = st.text_area("main_content", height=120)
        inputs["markdown_sections"] = st.text_area("markdown_sections (JSON)", height=80)
        inputs["code_example"]      = st.text_area("code_example", height=100)
        inputs["external_links"]    = st.text_area("external_links (JSON)", height=80)
        inputs["table_data"]        = st.text_area("table_data (JSON)", height=80)
        inputs["reference_links"]   = st.text_area("reference_links (JSON)", height=80)
        inputs["custom_module"]     = st.text_input("custom_module")
        inputs["display_order"]     = st.number_input("**display_order**", min_value=1, value=1)
        inputs["extra_html"]        = st.text_area("extra_html", height=80)
        inputs["prompt"]            = st.text_area("prompt", height=100)

        if st.form_submit_button("Save row"):
            if not (inputs["module"] and inputs["tab_number"] and inputs["title"]):
                st.error("module, tab_number, and title are required.")
            else:
                insert_tab(tuple(none_if_blank(inputs[c]) for c in COLS))
                st.success("Row saved!")

    st.divider()
    st.subheader("Existing rows")
    st.dataframe(fetch_tabs(), use_container_width=True)

# ───────────────────── 6. Edit page ────────────────────────────
def edit_page():
    st.title("Edit Existing Row")

    rows = fetch_tabs()
    if not rows:
        st.info("No data to edit.")
        return

    label = lambda r: f"{r['module']} | {r['tab_number']} | {r['title']}"
    selected = st.selectbox("Choose a row", rows, format_func=label)
    tab_id = selected["tab_id"]

    with st.form(f"edit_{tab_id}"):
        inputs = {}
        for col in COLS:
            if col in ("main_content", "markdown_sections", "code_example",
                       "external_links", "table_data", "reference_links",
                       "extra_html", "prompt"):
                height = 120 if col == "main_content" else 100
                height = 80 if col not in ("main_content", "code_example") else height
                inputs[col] = st.text_area(col, value=selected.get(col) or "", height=height)
            elif col == "display_order":
                inputs[col] = st.number_input(col, min_value=1, value=int(selected[col]))
            else:
                inputs[col] = st.text_input(col, value=selected.get(col) or "")

        if st.form_submit_button("Update row"):
            if not (inputs["module"] and inputs["tab_number"] and inputs["title"]):
                st.error("module, tab_number, and title are required.")
            else:
                update_tab(tab_id, tuple(none_if_blank(inputs[c]) for c in COLS))
                st.success("Row updated!")

# ───────────────────── 7. Bulk Upload page ─────────────────────
def bulk_page():
    st.title("Bulk CSV Upload")

    uploaded = st.file_uploader("Upload CSV", type="csv")
    if not uploaded:
        st.info("Awaiting CSV file.")
        return

    df = pd.read_csv(uploaded)
    st.write("Preview:")
    st.dataframe(df.head())

    # Ensure all expected columns exist; fill missing with None
    for col in COLS:
        if col not in df.columns:
            df[col] = None

    mode = st.radio("Insert mode", ("Insert new rows", "Update if tab_id present"))

    if st.button("Import"):
        inserted = updated = 0
        for _, r in df.iterrows():
            values = tuple(
                none_if_blank(r.get(col)) if col != "display_order"
                else int(r.get(col) or 1)
                for col in COLS
            )

            tab_id_val = int(r["tab_id"]) if "tab_id" in df.columns and pd.notna(r["tab_id"]) else None

            try:
                if mode == "Update if tab_id present" and tab_id_val:
                    update_tab(tab_id_val, values)
                    updated += 1
                else:
                    insert_tab(values)
                    inserted += 1
            except Exception as e:
                st.error(f"Error on row {_}: {e}")

        st.success(f"Inserted: {inserted}, Updated: {updated}")

# ───────────────────── 8. Guideline page ───────────────────────
def guideline_page():
    st.title("Row-wise Guideline")

    rows = fetch_tabs()
    if not rows:
        st.info("No data available.")
        return

    label = lambda r: f"{r['module']} | {r['tab_number']} | {r['title']}"
    selected = st.selectbox("Choose a row", rows, format_func=label)

    st.markdown("#### Raw JSON (copy-friendly)")
    st.code(json.dumps(selected, indent=2, ensure_ascii=False), language="json")

# ───────────────────── 9. Router ───────────────────────────────
if page == "Add":
    add_page()
elif page == "Edit":
    edit_page()
elif page == "Bulk Upload":
    bulk_page()
else:
    guideline_page()
