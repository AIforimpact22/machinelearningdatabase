# app_course_manager.py — unified UI for course_tabs & course_tasks with CSV-upload guidelines
import streamlit as st
import mysql.connector
import pandas as pd
import json, datetime, io
from typing import Any, Dict, List, Tuple

# ───────────────────── 1. MySQL connection ─────────────────────
@st.cache_resource
def get_conn():
    cfg = st.secrets["mysql"]
    return mysql.connector.connect(
        host=cfg["host"], port=int(cfg["port"]),
        user=cfg["user"], password=cfg["password"],
        database=cfg["database"], autocommit=True,
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
        "sample": [
            {
                "module": "Week 1",
                "tab_number": "tab1",
                "title": "Introduction to Python",
                "subtitle": "",
                "video_url": "https://youtu.be/abc123",
                "video_upload": "",
                "main_content": "Markdown body here",
                "markdown_sections": "",
                "code_example": "",
                "external_links": "",
                "table_data": "",
                "reference_links": "",
                "custom_module": "",
                "display_order": 1,
                "extra_html": "",
                "prompt": ""
            }
        ]
    },
    "course_tasks": {
        "pk": "task_id",
        "cols": [
            "tab_id","task_type","question","options_json","correct_answer",
            "assignment_details","solution","points","due_date"
        ],
        "required": ["tab_id","task_type","question"],
        "sample": [
            {
                "tab_id": 1,
                "task_type": "quiz",
                "question": "Which command mounts Google Drive in Colab?",
                "options_json": json.dumps([
                    "A. !pip install drive",
                    "B. from google.colab import drive\ndrive.mount('/content/drive')",
                    "C. import os",
                    "D. !gdown --id <id>"
                ]),
                "correct_answer": "B",
                "assignment_details": "",
                "solution": "Use drive.mount to attach Drive.",
                "points": 2,
                "due_date": ""
            }
        ]
    },
}

# ───────────────────── 4. Utility helpers ───────────────────────
def none_if_blank(v: Any) -> Any:
    if v is None: return None
    s = str(v).strip()
    return None if s == "" else v

def insert_row(table: str, values: Tuple):
    cols = TABLES[table]["cols"]
    with conn.cursor(buffered=True) as cur:
        cur.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))})",
            values,
        )

def update_row(table: str, pk_val: int, values: Tuple):
    cols = TABLES[table]["cols"]
    pk   = TABLES[table]["pk"]
    assignments = ", ".join(f"{c}=%s" for c in cols)
    with conn.cursor(buffered=True) as cur:
        cur.execute(
            f"UPDATE {table} SET {assignments} WHERE {pk}=%s",
            values + (pk_val,),
        )

def fetch_all(table: str) -> List[Dict]:
    with conn.cursor(buffered=True, dictionary=True) as cur:
        cur.execute(f"SELECT * FROM {table}")
        return cur.fetchall()

# ───────────────────── 5. Page & table selector ─────────────────
table_choice = st.sidebar.selectbox("Table", ("course_tabs", "course_tasks"))
page_choice  = st.sidebar.radio("Page", ("Add", "Edit", "Bulk Upload", "Guideline"))

META = TABLES[table_choice]
PK, COLS, REQ = META["pk"], META["cols"], set(META["required"])

# ───────────────────── 6. Add page ─────────────────────────────
def add_page():
    st.title(f"Add → {table_choice}")
    with st.form("add_form", clear_on_submit=True):
        inputs: Dict[str, Any] = {}
        for col in COLS:
            if col in ("main_content","markdown_sections","code_example",
                       "external_links","table_data","reference_links",
                       "assignment_details","solution","extra_html","prompt",
                       "question","options_json"):
                inputs[col] = st.text_area(col, height=120 if col=="main_content" else 90)
            elif col == "task_type":
                inputs[col] = st.selectbox(col, ("quiz","assignment"))
            elif col in ("points","display_order"):
                inputs[col] = st.number_input(col, min_value=1, value=1)
            elif col == "due_date":
                inputs[col] = st.date_input(col, value=datetime.date.today())
            else:
                inputs[col] = st.text_input(col)

        if st.form_submit_button("Save"):
            if not all(inputs[c] for c in REQ):
                st.error(f"Required: {', '.join(REQ)}")
            else:
                insert_row(table_choice, tuple(none_if_blank(inputs[c]) for c in COLS))
                st.success("Inserted.")

    st.divider()
    st.dataframe(fetch_all(table_choice), use_container_width=True)

# ───────────────────── 7. Edit page ────────────────────────────
def edit_page():
    st.title(f"Edit → {table_choice}")
    rows = fetch_all(table_choice)
    if not rows: st.info("No data."); return
    selected = st.selectbox("Row", rows, format_func=lambda r: f"{table_choice[:-1]} {r[PK]}")
    pk_val = selected[PK]
    with st.form(f"edit_{pk_val}"):
        inputs: Dict[str, Any] = {}
        for col in COLS:
            cur = selected.get(col)
            widget_kwargs = dict(value=cur or "")
            if col in ("main_content","markdown_sections","code_example",
                       "external_links","table_data","reference_links",
                       "assignment_details","solution","extra_html","prompt",
                       "question","options_json"):
                widget_kwargs["height"] = 120 if col=="main_content" else 90
                inputs[col] = st.text_area(col, **widget_kwargs)
            elif col == "task_type":
                inputs[col] = st.selectbox(col, ("quiz","assignment"), index=0 if cur=="quiz" else 1)
            elif col in ("points","display_order"):
                inputs[col] = st.number_input(col, min_value=1, value=int(cur or 1))
            elif col == "due_date":
                date_val = cur if isinstance(cur, datetime.date) else datetime.date.today()
                inputs[col] = st.date_input(col, value=date_val)
            else:
                inputs[col] = st.text_input(col, **widget_kwargs)

        if st.form_submit_button("Update"):
            if not all(inputs[c] for c in REQ):
                st.error(f"Required: {', '.join(REQ)}")
            else:
                update_row(table_choice, pk_val, tuple(none_if_blank(inputs[c]) for c in COLS))
                st.success("Updated.")

# ───────────────────── 8. Bulk Upload page ─────────────────────
def bulk_page():
    st.title(f"Bulk CSV → {table_choice}")

    # 8a. Guideline block
    st.markdown("##### CSV template")
    sample_df = pd.DataFrame(META["sample"])
    buf = io.StringIO()
    sample_df.to_csv(buf, index=False)
    st.code(buf.getvalue(), language="csv")
    st.download_button("Download sample CSV", data=buf.getvalue(), file_name=f"{table_choice}_sample.csv")

    # 8b. Uploader
    file = st.file_uploader("Upload your CSV", type="csv")
    if not file: return

    df = pd.read_csv(file)
    st.markdown("Preview:")
    st.dataframe(df.head())

    # add missing cols
    for col in COLS:
        if col not in df.columns: df[col] = None

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
                    update_row(table_choice, pk_val, vals)
                    upd += 1
                else:
                    insert_row(table_choice, vals)
                    ins += 1
            except Exception as e:
                st.error(f"Row {idx} error: {e}")
        st.success(f"Inserted: {ins} | Updated: {upd}")

# ───────────────────── 9. Guideline page ───────────────────────
def guideline_page():
    st.title(f"Guideline → {table_choice}")
    rows = fetch_all(table_choice)
    if not rows: st.info("No data."); return
    selected = st.selectbox("Row", rows, format_func=lambda r: f"{table_choice[:-1]} {r[PK]}")
    st.code(json.dumps(selected, indent=2, default=str), language="json")

# ───────────────────── 10. Router ──────────────────────────────
if page_choice == "Add":
    add_page()
elif page_choice == "Edit":
    edit_page()
elif page_choice == "Bulk Upload":
    bulk_page()
else:
    guideline_page()
