# app_course_tabs.py  — Add • Edit • Guideline (robust, buffered cursors)
import streamlit as st
import mysql.connector
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

# ───────────────────── 2. Ensure table (buffered cursor) ───────
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
def none_if_blank(v: str | None) -> Any:
    return None if (v is None or not v.strip()) else v

def insert_tab(row: Tuple):
    with conn.cursor(buffered=True) as cur:
        cur.execute(
            """
            INSERT INTO course_tabs
            (module, tab_number, title, subtitle, video_url, video_upload,
             main_content, markdown_sections, code_example, external_links,
             table_data, reference_links, custom_module, display_order,
             extra_html, prompt)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            row,
        )

def update_tab(tab_id: int, row: Tuple):
    with conn.cursor(buffered=True) as cur:
        cur.execute(
            """
            UPDATE course_tabs SET
              module=%s, tab_number=%s, title=%s, subtitle=%s, video_url=%s,
              video_upload=%s, main_content=%s, markdown_sections=%s,
              code_example=%s, external_links=%s, table_data=%s,
              reference_links=%s, custom_module=%s, display_order=%s,
              extra_html=%s, prompt=%s
            WHERE tab_id=%s
            """,
            row + (tab_id,),
        )

def fetch_tabs() -> List[Dict]:
    with conn.cursor(buffered=True, dictionary=True) as cur:
        cur.execute("SELECT * FROM course_tabs ORDER BY module, display_order, tab_number")
        return cur.fetchall()

# ───────────────────── 4. Page selector ────────────────────────
page = st.sidebar.radio("Page", ("Add", "Edit", "Guideline"))

# ───────────────────── 5. Add page ─────────────────────────────
def add_page():
    st.title("Add New Row")

    with st.form("add_row", clear_on_submit=True):
        module         = st.text_input("**module**")
        tab_number     = st.text_input("**tab_number**")
        title          = st.text_input("**title**")
        subtitle       = st.text_input("subtitle")
        video_url      = st.text_input("video_url")
        video_upload   = st.text_input("video_upload")
        main_content   = st.text_area("main_content", height=120)
        markdown_sections = st.text_area("markdown_sections (JSON)", height=80)
        code_example   = st.text_area("code_example", height=100)
        external_links = st.text_area("external_links (JSON)", height=80)
        table_data     = st.text_area("table_data (JSON)", height=80)
        reference_links= st.text_area("reference_links (JSON)", height=80)
        custom_module  = st.text_input("custom_module")
        display_order  = st.number_input("**display_order**", min_value=1, value=1)
        extra_html     = st.text_area("extra_html", height=80)
        prompt         = st.text_area("prompt", height=100)

        if st.form_submit_button("Save row"):
            if not (module and tab_number and title):
                st.error("module, tab_number, and title are required.")
            else:
                insert_tab(
                    (
                        module, tab_number, title, none_if_blank(subtitle),
                        none_if_blank(video_url), none_if_blank(video_upload),
                        none_if_blank(main_content), none_if_blank(markdown_sections),
                        none_if_blank(code_example), none_if_blank(external_links),
                        none_if_blank(table_data), none_if_blank(reference_links),
                        none_if_blank(custom_module), int(display_order),
                        none_if_blank(extra_html), none_if_blank(prompt),
                    )
                )
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
        module         = st.text_input("module",           value=selected["module"])
        tab_number     = st.text_input("tab_number",       value=selected["tab_number"])
        title          = st.text_input("title",            value=selected["title"])
        subtitle       = st.text_input("subtitle",         value=selected.get("subtitle") or "")
        video_url      = st.text_input("video_url",        value=selected.get("video_url") or "")
        video_upload   = st.text_input("video_upload",     value=selected.get("video_upload") or "")
        main_content   = st.text_area("main_content",      value=selected.get("main_content") or "", height=120)
        markdown_sections = st.text_area("markdown_sections (JSON)", value=selected.get("markdown_sections") or "", height=80)
        code_example   = st.text_area("code_example",      value=selected.get("code_example") or "", height=100)
        external_links = st.text_area("external_links (JSON)", value=selected.get("external_links") or "", height=80)
        table_data     = st.text_area("table_data (JSON)", value=selected.get("table_data") or "", height=80)
        reference_links= st.text_area("reference_links (JSON)", value=selected.get("reference_links") or "", height=80)
        custom_module  = st.text_input("custom_module",    value=selected.get("custom_module") or "")
        display_order  = st.number_input("display_order",  min_value=1, value=int(selected["display_order"]))
        extra_html     = st.text_area("extra_html",        value=selected.get("extra_html") or "", height=80)
        prompt         = st.text_area("prompt",            value=selected.get("prompt") or "", height=100)

        if st.form_submit_button("Update row"):
            if not (module and tab_number and title):
                st.error("module, tab_number, and title are required.")
            else:
                update_tab(
                    tab_id,
                    (
                        module, tab_number, title, none_if_blank(subtitle),
                        none_if_blank(video_url), none_if_blank(video_upload),
                        none_if_blank(main_content), none_if_blank(markdown_sections),
                        none_if_blank(code_example), none_if_blank(external_links),
                        none_if_blank(table_data), none_if_blank(reference_links),
                        none_if_blank(custom_module), int(display_order),
                        none_if_blank(extra_html), none_if_blank(prompt),
                    ),
                )
                st.success("Row updated!")

# ───────────────────── 7. Guideline page ───────────────────────
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

# ───────────────────── 8. Router ───────────────────────────────
if page == "Add":
    add_page()
elif page == "Edit":
    edit_page()
else:
    guideline_page()
