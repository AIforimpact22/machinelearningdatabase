# app_course_manager.py  — unified UI for course_tabs & course_tasks
import streamlit as st
import mysql.connector
import pandas as pd
import json
import datetime
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

# ───────────────────── 2. Ensure tables ─────────────────────────
with conn.cursor(buffered=True) as cur:
    cur.execute(
        """
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
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS course_tasks (
          task_id INT AUTO_INCREMENT PRIMARY KEY,
          tab_id INT NOT NULL,
          task_type ENUM('quiz','assignment') NOT NULL,
          question TEXT,
          options_json TEXT,
          correct_answer TEXT,
          assignment_details TEXT,
          solution TEXT,
          points INT DEFAULT 1,
          due_date DATE,
          FOREIGN KEY (tab_id) REFERENCES course_tabs(tab_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

# ───────────────────── 3. Metadata per table ────────────────────
TABLES: Dict[str, Dict] = {
    "course_tabs": {
        "pk": "tab_id",
        "cols": [
            "module","tab_number","title","subtitle","video_url","video_upload",
            "main_content","markdown_sections","code_example","external_links",
            "table_data","reference_links","custom_module","display_order",
            "extra_html","prompt"
        ],
        "required": ["module","tab_number","title"],
        "csv_example": """module,tab_number,title,subtitle,video_url,video_upload,main_content,markdown_sections,code_example,external_links,table_data,reference_links,custom_module,display_order,extra_html,prompt
Week 1,tab1,Intro to Python,,,,,"# Welcome to Python",,,,"",,,1,,"""
    },
    "course_tasks": {
        "pk": "task_id",
        "cols": [
            "tab_id","task_type","question","options_json","correct_answer",
            "assignment_details","solution","points","due_date"
        ],
        "required": ["tab_id","task_type","question"],
        "csv_example": """tab_id,task_type,question,options_json,correct_answer,assignment_details,solution,points,due_date
6,quiz,"Which Pandas command reads a CSV?","[""A. read_table()"",""B. pd.read_csv()""]","B",,,""",1,"""
    },
}

# ───────────────────── 4. Utility helpers ───────────────────────
def none_if_blank(v: Any) -> Any:
    if v is None: return None
    s = str(v).strip()
    return None if s == "" else v

def insert_row(table: str, values: Tuple):
    with conn.cursor(buffered=True) as cur:
        cols = TABLES[table]["cols"]
        cur.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))})",
            values,
        )

def update_row(table: str, pk_val: int, values: Tuple):
    with conn.cursor(buffered=True) as cur:
        cols = TABLES[table]["cols"]
        assignments = ", ".join(f"{c}=%s" for c in cols)
        pk_col = TABLES[table]["pk"]
        cur.execute(
            f"UPDATE {table} SET {assignments} WHERE {pk_col}=%s",
            values + (pk_val,),
        )

def fetch_all(table: str) -> List[Dict]:
    with conn.cursor(buffered=True, dictionary=True) as cur:
        cur.execute(f"SELECT * FROM {table}")
        return cur.fetchall()

# ───────────────────── 5. Page & table selector ─────────────────
table_choice = st.sidebar.selectbox("Choose table", ("course_tabs", "course_tasks"))
page = st.sidebar.radio("Page", ("Add", "Edit", "Bulk Upload", "Guideline"))

META = TABLES[table_choice]
PK   = META["pk"]
COLS = META["cols"]
REQ  = set(META["required"])

# ───────────────────── 6. Add page ─────────────────────────────
def add_page():
    st.title(f"Add → {table_choice}")

    with st.form("add_form", clear_on_submit=True):
        inputs: Dict[str, Any] = {}
        for col in COLS:
            if col in ("main_content","markdown_sections","code_example",
                       "external_links","table_data","reference_links",
                       "assignment_details","solution","extra_html","prompt","question","options_json"):
                height = 120 if col in ("main_content","assignment_details") else 90
                inputs[col] = st.text_area(col, height=height)
            elif col == "task_type":
                inputs[col] = st.selectbox(col, ("quiz","assignment"))
            elif col == "points":
                inputs[col] = st.number_input(col, min_value=1, value=1)
            elif col == "display_order":
                inputs[col] = st.number_input(col, min_value=1, value=1)
            elif col == "due_date":
                inputs[col] = st.date_input(col, value=None)
            else:
                inputs[col] = st.text_input(col)

        if st.form_submit_button("Save"):
            if not all(inputs[c] for c in REQ):
                st.error(f"Required fields: {', '.join(REQ)}")
            else:
                vals = tuple(none_if_blank(inputs[c]) for c in COLS)
                insert_row(table_choice, vals)
                st.success("Row inserted.")

    st.divider()
    st.subheader("Preview")
    st.dataframe(fetch_all(table_choice), use_container_width=True)

# ───────────────────── 7. Edit page ────────────────────────────
def edit_page():
    st.title(f"Edit → {table_choice}")

    rows = fetch_all(table_choice)
    if not rows:
        st.info("No data.")
        return

    label = lambda r: f"{table_choice[:-1]} {r[PK]}"
    selected = st.selectbox("Select row", rows, format_func=label)
    pk_val = selected[PK]

    with st.form(f"edit_{pk_val}"):
        inputs: Dict[str, Any] = {}
        for col in COLS:
            current = selected.get(col)
            if col in ("main_content","markdown_sections","code_example",
                       "external_links","table_data","reference_links",
                       "assignment_details","solution","extra_html","prompt","question","options_json"):
                height = 120 if col in ("main_content","assignment_details") else 90
                inputs[col] = st.text_area(col, value=current or "", height=height)
            elif col == "task_type":
                inputs[col] = st.selectbox(col, ("quiz","assignment"), index=0 if current=="quiz" else 1)
            elif col == "points":
                inputs[col] = st.number_input(col, min_value=1, value=int(current or 1))
            elif col == "display_order":
                inputs[col] = st.number_input(col, min_value=1, value=int(current or 1))
            elif col == "due_date":
                date_val = current if isinstance(current, datetime.date) else None
                inputs[col] = st.date_input(col, value=date_val)
            else:
                inputs[col] = st.text_input(col, value=current or "")

        if st.form_submit_button("Update"):
            if not all(inputs[c] for c in REQ):
                st.error(f"Required fields: {', '.join(REQ)}")
            else:
                vals = tuple(none_if_blank(inputs[c]) for c in COLS)
                update_row(table_choice, pk_val, vals)
                st.success("Row updated.")

# ───────────────────── 8. Bulk Upload page ─────────────────────
def bulk_page():
    st.title(f"Bulk CSV → {table_choice}")

    st.markdown("##### Expected CSV header")
    st.code(",".join(COLS), language="csv")

    st.markdown("##### Minimal example")
    st.code(META["csv_example"], language="csv")

    file = st.file_uploader("Upload CSV file", type="csv")
    if not file:
        return

    df = pd.read_csv(file)
    st.dataframe(df.head())

    for col in COLS:
        if col not in df.columns:
            df[col] = None

    mode = st.radio("Mode", ("Insert only", "Update if PK present"))

    if st.button("Import"):
        ins = upd = 0
        for idx, r in df.iterrows():
            vals = []
            for col in COLS:
                val = r.get(col)
                if col in ("display_order","points") and pd.notna(val):
                    val = int(val)
                vals.append(none_if_blank(val))
            vals_t = tuple(vals)

            pk_val = int(r[PK]) if (PK in df.columns and pd.notna(r[PK])) else None
            try:
                if mode == "Update if PK present" and pk_val:
                    update_row(table_choice, pk_val, vals_t)
                    upd += 1
                else:
                    insert_row(table_choice, vals_t)
                    ins += 1
            except Exception as e:
                st.error(f"Row {idx} error: {e}")
        st.success(f"Inserted {ins}, Updated {upd}")

# ───────────────────── 9. Guideline page ───────────────────────
def guideline_page():
    st.title(f"Guideline → {table_choice}")

    rows = fetch_all(table_choice)
    if not rows:
        st.info("No data.")
        return

    selected = st.selectbox("Row", rows, format_func=lambda r: f"{table_choice[:-1]} {r[PK]}")
    st.code(json.dumps(selected, indent=2, default=str), language="json")

# ───────────────────── 10. Router ──────────────────────────────
if page == "Add":
    add_page()
elif page == "Edit":
    edit_page()
elif page == "Bulk Upload":
    bulk_page()
else:
    guideline_page()
