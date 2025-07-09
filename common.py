import streamlit as st
import mysql.connector, json, datetime, io
from typing import Any, Dict, List, Tuple
import pandas as pd   # only needed for bulk.py

# ─────────────────── 1. MySQL connection ────────────────────
@st.cache_resource
def get_conn():
    cfg = st.secrets["mysql"]
    return mysql.connector.connect(
        host     = cfg["host"],
        port     = int(cfg["port"]),
        user     = cfg["user"],
        password = cfg["password"],
        database = cfg["database"],
        autocommit=True,
    )

conn = get_conn()

# ─────────────────── 2. Ensure tables exist ─────────────────
with conn.cursor(buffered=True) as cur:
    cur.execute("""                     -- course_tabs
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
    )
    cur.execute("""                     -- course_tasks
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
    )

# ─────────────────── 3. Metadata per table ──────────────────
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

# ─────────────────── 4. Helper functions ────────────────────
def none_if_blank(v: Any) -> Any:
    if v is None: 
        return None
    s = str(v).strip()
    return None if s == "" else v

def insert_row(table: str, values: Tuple):
    cols = TABLES[table]["cols"]
    ph   = ", ".join(["%s"] * len(cols))
    with conn.cursor(buffered=True) as cur:
        cur.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({ph})", values)

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

# ─────────────────── 5. Sidebar helper ──────────────────────
def table_selector() -> str:
    """Return the current table and keep the choice in session_state
       so all pages stay in sync."""
    options = list(TABLES.keys())
    if "table_choice" not in st.session_state:
        st.session_state.table_choice = options[0]
    chosen = st.sidebar.selectbox("Table", options, 
                                  index=options.index(st.session_state.table_choice))
    st.session_state.table_choice = chosen
    return chosen
