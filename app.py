import streamlit as st
import mysql.connector
import json

# ------------------------------------------------------------------ #
# 1. Connect and guarantee the course_tabs table exists
# ------------------------------------------------------------------ #
@st.cache_resource  # keeps one connection across reruns
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        autocommit=True
    )

conn = get_connection()
cur  = conn.cursor()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS course_tabs (
    tab_id INT AUTO_INCREMENT PRIMARY KEY,
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
);
"""
cur.execute(CREATE_TABLE_SQL)
cur.close()

# ------------------------------------------------------------------ #
# 2. Helpers
# ------------------------------------------------------------------ #
def insert_tab(row):
    with conn.cursor() as c:
        c.execute(
            """
            INSERT INTO course_tabs
            (tab_number,title,subtitle,video_url,video_upload,
             main_content,markdown_sections,code_example,
             external_links,table_data,reference_links,
             custom_module,display_order,extra_html,prompt)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            row,
        )

def fetch_tabs():
    with conn.cursor(dictionary=True) as c:
        c.execute("SELECT * FROM course_tabs ORDER BY display_order;")
        return c.fetchall()

# ------------------------------------------------------------------ #
# 3. Streamlit UI
# ------------------------------------------------------------------ #
st.title("Course Tabs Admin")

with st.form("new_tab", clear_on_submit=True):
    st.subheader("Add / Update Tab")

    tab_number   = st.text_input("Tab number (e.g. 1.1)")
    title        = st.text_input("Title")
    subtitle     = st.text_input("Subtitle (optional)")
    video_url    = st.text_input("Video URL (YouTube etc.)")
    video_upload = st.text_input("Video upload path / URL")
    main_content = st.text_area("Main content (Markdown)", height=150)
    markdown_sections = st.text_area(
        "Markdown sections (JSON list)",
        placeholder='[{"header":"Section A","content":"..."}]',
        height=100
    )
    code_example = st.text_area("Code example", height=120)
    external_links = st.text_area(
        "External links (JSON list)",
        placeholder='[{"title":"Link","url":"https://..."}]',
        height=80
    )
    table_data  = st.text_area("Table data (JSON)", height=80)
    reference_links = st.text_area("Reference links (JSON)", height=80)
    custom_module = st.text_input("Custom module (e.g. as1)")
    display_order = st.number_input("Display order", min_value=1, step=1, value=1)
    extra_html    = st.text_area("Extra HTML", height=80)
    prompt        = st.text_area("ChatGPT prompt", height=120)

    if st.form_submit_button("Save"):
        try:
            insert_tab(
                (
                    tab_number, title, subtitle, video_url, video_upload,
                    main_content, markdown_sections, code_example,
                    external_links, table_data, reference_links,
                    custom_module, int(display_order), extra_html, prompt
                )
            )
            st.success(f"Saved tab {tab_number}")
        except Exception as e:
            st.error(f"Insert failed: {e}")

st.divider()
st.subheader("Existing Tabs")
tabs = fetch_tabs()
if tabs:
    st.dataframe(tabs, use_container_width=True)
else:
    st.info("No tabs yet.")
