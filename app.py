import streamlit as st
import mysql.connector
import json

# ---- Database connection ----------------------------------------------------
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
cur = conn.cursor(dictionary=True)

# ---- Helpers ----------------------------------------------------------------
def insert_tab(row):
    insert_sql = """
        INSERT INTO course_tabs
        (tab_number, title, subtitle, video_url, video_upload,
         main_content, markdown_sections, code_example,
         external_links, table_data, reference_links,
         custom_module, display_order, extra_html, prompt)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cur.execute(insert_sql, row)

def fetch_tabs():
    cur.execute("SELECT * FROM course_tabs ORDER BY display_order;")
    return cur.fetchall()

# ---- UI ---------------------------------------------------------------------
st.title("Course-Tabs Admin")

with st.form("new_tab", clear_on_submit=True):
    st.subheader("Add / Update a Tab")
    tab_number  = st.text_input("Tab number (e.g. 1.1)")
    title       = st.text_input("Title")
    subtitle    = st.text_input("Subtitle (optional)")
    video_url   = st.text_input("Video URL (YouTube, etc.)")
    video_upload= st.text_input("Video upload path / URL (optional)")
    main_content= st.text_area("Main content (Markdown)", height=150)
    markdown_sections = st.text_area("Markdown sections (JSON list)", height=100,
        placeholder='[{"header":"Section A","content":"..."}]')
    code_example = st.text_area("Code example (raw text)", height=120)
    external_links = st.text_area("External links (JSON list)", height=80,
        placeholder='[{"title":"Link 1","url":"https://..."}]')
    table_data  = st.text_area("Table data (JSON, optional)", height=80)
    reference_links = st.text_area("Reference links (JSON, optional)", height=80)
    custom_module = st.text_input("Custom module (e.g. as1)")
    display_order = st.number_input("Display order", min_value=1, step=1, value=1)
    extra_html  = st.text_area("Extra HTML (optional)", height=80)
    prompt      = st.text_area("ChatGPT prompt", height=120)

    submitted = st.form_submit_button("Save to database")
    if submitted:
        try:
            row = (
                tab_number, title, subtitle, video_url, video_upload,
                main_content, markdown_sections, code_example,
                external_links, table_data, reference_links,
                custom_module, int(display_order), extra_html, prompt
            )
            insert_tab(row)
            st.success(f"Saved tab {tab_number}")
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.subheader("Existing Tabs")
tabs = fetch_tabs()
if tabs:
    st.dataframe(tabs, use_container_width=True)
else:
    st.info("No tabs in database yet.")
