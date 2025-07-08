# app_course_tabs.py
import streamlit as st
import mysql.connector
from typing import Any

# ------------------------------------------------------------------ #
# 1. DB connection and table guarantee
# ------------------------------------------------------------------ #
@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        autocommit=True,
    )

conn = get_connection()
cur  = conn.cursor()
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS course_tabs (
      tab_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
      module VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
      tab_number VARCHAR(10) COLLATE utf8mb4_unicode_ci NOT NULL,
      title VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
      subtitle VARCHAR(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
      video_url VARCHAR(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
      video_upload VARCHAR(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
      main_content TEXT COLLATE utf8mb4_unicode_ci,
      markdown_sections TEXT COLLATE utf8mb4_unicode_ci,
      code_example TEXT COLLATE utf8mb4_unicode_ci,
      external_links TEXT COLLATE utf8mb4_unicode_ci,
      table_data TEXT COLLATE utf8mb4_unicode_ci,
      reference_links TEXT COLLATE utf8mb4_unicode_ci,
      custom_module VARCHAR(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
      display_order INT NOT NULL,
      extra_html TEXT COLLATE utf8mb4_unicode_ci,
      prompt TEXT COLLATE utf8mb4_unicode_ci
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
)
cur.close()


# ------------------------------------------------------------------ #
# 2. Helpers
# ------------------------------------------------------------------ #
def none_if_blank(value: str) -> Any:
    """Return None for blank strings (to store as SQL NULL)."""
    return None if not value.strip() else value

def insert_tab(row):
    with conn.cursor() as c:
        c.execute(
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

def fetch_tabs():
    with conn.cursor(dictionary=True) as c:
        c.execute(
            "SELECT * FROM course_tabs ORDER BY module, display_order, tab_number;"
        )
        return c.fetchall()


# ------------------------------------------------------------------ #
# 3. Streamlit UI
# ------------------------------------------------------------------ #
st.title("Course Tabs Admin")

with st.form("new_tab", clear_on_submit=True):
    st.markdown("Fields marked **bold** are required.")
    module        = st.text_input("**Module** (e.g. week1, ML101)")
    tab_number    = st.text_input("**Tab number** (e.g. 1.1)")
    title         = st.text_input("**Title**")
    subtitle      = st.text_input("Subtitle")
    video_url     = st.text_input("Video URL")
    video_upload  = st.text_input("Video upload path / URL")
    main_content  = st.text_area("Main content (Markdown)", height=140)
    markdown_sections = st.text_area("Markdown sections (JSON list)", height=90)
    code_example  = st.text_area("Code example", height=110)
    external_links = st.text_area("External links (JSON list)", height=70)
    table_data    = st.text_area("Table data (JSON)", height=70)
    reference_links = st.text_area("Reference links (JSON)", height=70)
    custom_module = st.text_input("Custom module")
    display_order = st.number_input("**Display order**", min_value=1, step=1, value=1)
    extra_html    = st.text_area("Extra HTML", height=70)
    prompt        = st.text_area("ChatGPT prompt", height=110)

    if st.form_submit_button("Save"):
        # basic validation for required fields
        if not module.strip() or not tab_number.strip() or not title.strip():
            st.error("Please fill in all required fields (bold labels).")
        else:
            try:
                insert_tab(
                    (
                        module.strip(),
                        tab_number.strip(),
                        title.strip(),
                        none_if_blank(subtitle),
                        none_if_blank(video_url),
                        none_if_blank(video_upload),
                        none_if_blank(main_content),
                        none_if_blank(markdown_sections),
                        none_if_blank(code_example),
                        none_if_blank(external_links),
                        none_if_blank(table_data),
                        none_if_blank(reference_links),
                        none_if_blank(custom_module),
                        int(display_order),
                        none_if_blank(extra_html),
                        none_if_blank(prompt),
                    )
                )
                st.success(f"Saved tab {module.strip()} – {tab_number.strip()}")
            except Exception as e:
                st.error(f"Insert failed: {e}")

st.divider()
st.subheader("Existing Tabs")
tabs = fetch_tabs()
if tabs:
    st.dataframe(tabs, use_container_width=True)
else:
    st.info("No tabs yet.")
