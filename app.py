# app_course_data.py  — Add • Edit • Guideline • Bulk Upload (tabs + tasks)
import streamlit as st
import mysql.connector
import pandas as pd
import json
from typing import Any, Dict, List, Tuple

# ───────────────── 1. MySQL connection ────────────────
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

# ───────────────── 2. Ensure both tables ──────────────
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

# ───────────────── 3. Column configs ─────────────────
COLS_TABS = [
    "module","tab_number","title","subtitle","video_url","video_upload",
    "main_content","markdown_sections","code_example","external_links",
    "table_data","reference_links","custom_module","display_order",
    "extra_html","prompt"
]

COLS_TASKS = [
    "tab_id","task_type","question","options_json","correct_answer",
    "assignment_details","solution","points","due_date"
]

def none_if_blank(v: Any) -> Any:
    return None if (v is None or str(v).strip() == "") else v

# ───────────────── 4. Generic DB helpers ─────────────
def insert_row(table: str, cols: List[str], values: Tuple):
    with conn.cursor(buffered=True) as cur:
        cur.execute(
            f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})",
            values,
        )

def update_row(table: str, pk_col: str, pk_val: int, cols: List[str], values: Tuple):
    assignments = ",".join(f"{c}=%s" for c in cols)
    with conn.cursor(buffered=True) as cur:
        cur.execute(
            f"UPDATE {table} SET {assignments} WHERE {pk_col}=%s",
            values + (pk_val,),
        )

def fetch_all(table: str) -> List[Dict]:
    with conn.cursor(buffered=True, dictionary=True) as cur:
        cur.execute(f"SELECT * FROM {table}")
        return cur.fetchall()

# ───────────────── 5. Bulk Upload page ───────────────
def bulk_page():
    st.title("Bulk CSV Upload")

    table_choice = st.selectbox("Target table", ("course_tabs", "course_tasks"))
    cols = COLS_TABS if table_choice == "course_tabs" else COLS_TASKS
    pk   = "tab_id" if table_choice == "course_tabs" else "task_id"

    uploaded = st.file_uploader("Upload CSV", type="csv")
    if not uploaded:
        st.info("Awaiting CSV file.")
        return

    df = pd.read_csv(uploaded)
    st.dataframe(df.head())

    # add missing cols as blank
    for c in cols:
        if c not in df.columns:
            df[c] = None

    mode = st.radio("Insert mode", ("Insert new", "Update if primary key present"))

    if st.button("Import"):
        ins = upd = 0
        for _, r in df.iterrows():
            vals = tuple(
                none_if_blank(r.get(c)) if c not in ("display_order","points") else int(r.get(c) or 1)
                for c in cols
            )
            pk_val = int(r[pk]) if pk in df.columns and pd.notna(r[pk]) else None
            try:
                if mode == "Update if primary key present" and pk_val:
                    update_row(table_choice, pk, pk_val, cols, vals)
                    upd += 1
                else:
                    insert_row(table_choice, cols, vals)
                    ins += 1
            except Exception as e:
                st.error(f"Row {_} error: {e}")
        st.success(f"Inserted {ins}, Updated {upd}")

# ───────────────── 6. Simple router (Bulk only shown here) ─────
if __name__ == "__main__":
    page = st.sidebar.radio("Page", ("Bulk Upload",))
    bulk_page()
