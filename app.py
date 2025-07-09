# app_course_tabs.py  — Admin + Copy-Friendly Guideline
import streamlit as st
import mysql.connector
import json
from typing import Any, List, Dict

# ───────────────────────────── 1. DB connection ──────────────────────────────
@st.cache_resource
def get_connection():
    cfg = st.secrets["mysql"]
    return mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        autocommit=True,
    )

conn = get_connection()

# ───────────────────────────── 2. Table guarantee ────────────────────────────
with conn.cursor() as cur:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS course_tabs (
          tab_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
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

# ───────────────────────────── 3. Helpers ────────────────────────────────────
def none_if_blank(v: str) -> Any:
    return None if not v.strip() else v

def insert_tab(row: tuple):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO course_tabs
            (module, tab_number, title, subtitle, video_url, video_upload,
             main_content, markdown_sections, code_example,
             external_links, table_data, reference_links,
             custom_module, display_order, extra_html, prompt)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            row,
        )

def fetch_tabs() -> List[Dict]:
    with conn.cursor(dictionary=True) as cur:
        cur.execute(
            "SELECT * FROM course_tabs ORDER BY module, display_order, tab_number;"
        )
        return cur.fetchall()

COLUMN_DESC = {
    "module":           "Logical grouping, e.g. 'Week 1'",
    "tab_number":       "Unique ID inside module, e.g. 'tab1'",
    "title":            "Main header",
    "subtitle":         "Secondary header",
    "video_url":        "YouTube / Vimeo link",
    "video_upload":     "Path / URL of uploaded video",
    "main_content":     "Markdown body",
    "markdown_sections":"JSON list of {header, content}",
    "code_example":     "Plain-text code snippet",
    "external_links":   "JSON list of {title, url}",
    "table_data":       "JSON table",
    "reference_links":  "JSON references",
    "custom_module":    "Python module name to import",
    "display_order":    "Integer for sorting",
    "extra_html":       "Raw HTML goodies",
    "prompt":           "ChatGPT prompt text",
}

# ───────────────────────────── 4. Page switcher ──────────────────────────────
page = st.sidebar.radio("Page", ("Admin", "Guideline"))

# ───────────────────────────── 5. Admin page ─────────────────────────────────
if page == "Admin":
    st.title("Course Tabs Admin")

    with st.form(key="add_row", clear_on_submit=True):
        st.markdown("Required fields are **bold**.")
        module         = st.text_input("**module**")
        tab_number     = st.text_input("**tab_number**")
        title          = st.text_input("**title**")
        subtitle       = st.text_input("subtitle")
        video_url      = st.text_input("video_url")
        video_upload   = st.text_input("video_upload")
        main_content   = st.text_area("main_content", height=140)
        markdown_sections = st.text_area("markdown_sections (JSON)", height=80)
        code_example   = st.text_area("code_example", height=100)
        external_links = st.text_area("external_links (JSON)", height=70)
        table_data     = st.text_area("table_data (JSON)", height=70)
        reference_links= st.text_area("reference_links (JSON)", height=70)
        custom_module  = st.text_input("custom_module")
        display_order  = st.number_input("**display_order**", min_value=1, value=1)
        extra_html     = st.text_area("extra_html", height=70)
        prompt         = st.text_area("prompt", height=100)

        if st.form_submit_button("Save row"):
            if not (module and tab_number and title):
                st.error("Fill in module, tab_number and title.")
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
                st.success("Row saved.")

    st.divider()
    st.subheader("Existing rows")
    rows = fetch_tabs()
    st.dataframe(rows, use_container_width=True) if rows else st.info("No rows yet.")

# ───────────────────────────── 6. Guideline page ─────────────────────────────
else:
    st.title("Row-Wise Guideline")

    rows = fetch_tabs()
    if not rows:
        st.info("No data available. Add something in Admin first.")
        st.stop()

    # Select row to inspect
    label = lambda r: f"{r['module']} | {r['tab_number']} | {r['title']}"
    choice = st.selectbox("Choose a row", options=rows, format_func=label)
    row = choice

    # 6a. Quick JSON block (easy to copy into ChatGPT)
    st.markdown("#### Raw JSON (copy-paste friendly)")
    st.code(json.dumps(row, indent=2), language="json")

    # 6b. Column explanations with current value
    st.markdown("#### Column-by-column guide")
    for col, desc in COLUMN_DESC.items():
        val = row.get(col)
        printable = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)
        st.markdown(f"- **{col}** → `{printable}`  \n  _{desc}_")
