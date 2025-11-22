import os
import time
import streamlit as st
import pandas as pd
import uuid
import sys
import unicodedata

from Core.Enums.database import DataTypeIconMap, DatabaseType
from Core.Enums.llm_provider import LLMProviderType
from Core.Enums.vectorstore import VectorStoreType

from Core.Repository.database import DatabaseRepository
from Core.Repository.llm_provider import LLMProviderRepository
from Core.Repository.vectorstore import VectorStoreRepository

from Core.Utils.logger import Logger
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import (
    DatabaseConnectionError,
    VectorstoreError,
)
from Core.Utils.helper import Helper

logger = Logger.get_logger()

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


class App:
    def __init__(self):
        self.db = None
        self.vectorstore = None
        self.llm = None
        self.config = {}
        self.unique_suffix = ""

    @exception_handler(show_ui=True)
    def main(self) -> None:
        # Set the page config
        st.set_page_config(page_title="Text-To-SQL Query Explorer", layout="centered")
        logger.info("App started")

        # ---------------- Load Font Awesome ----------------
        st.markdown(
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">',
            unsafe_allow_html=True,
        )

        # Init session state flags
        if "connected" not in st.session_state:
            st.session_state.connected = False

        if "db_uploaded" not in st.session_state:
            st.session_state.db_uploaded = False
            
        if "db_name" not in st.session_state:
            st.session_state.db_name = None

        # Page-wide wrapper to align header → content → footer vertically
        with st.container():
            st.markdown('<div class="main-container">', unsafe_allow_html=True)
            self.header()
            self.process_query_ui()
            st.markdown("</div>", unsafe_allow_html=True)

        self.sidebar()
        self.load_tooltip()

    @exception_handler(show_ui=True)
    def load_tooltip(self) -> None:
        # Add floating tooltip bottom-right
        st.markdown(
            """
            <style>
            .floating-tooltip {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(255, 255, 255, 0.15);
                color: #fff;
                padding: 10px 14px;
                border-radius: 10px;
                font-size: 13px;
                backdrop-filter: blur(6px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                z-index: 999999;
                animation: fadeOut 1s ease-in-out 4s forwards;
            }

            @keyframes fadeOut {
                to {
                    opacity: 0;
                    visibility: hidden;
                }
            }

            .floating-tooltip i {
                color: #ff6b6b;
                margin-right: 6px;
            }
            </style>

            <div class="floating-tooltip">
                <i class="fas fa-info-circle"></i>
                AI-generated SQL queries may sometimes produce incorrect output.
            </div>
            """,
            unsafe_allow_html=True
        )

    @exception_handler(show_ui=True)
    def header(self) -> None:
        # ---------------- Header ----------------
        st.markdown(
            """
            <h1 style="display:flex; align-items:center; gap:10px;">
                <i class="fas fa-database"></i> Text-To-SQL Query Explorer
            </h1>
            """,
            unsafe_allow_html=True,
        )
        st.write("Select a database, connect, and ask questions in plain English.")

    @exception_handler(show_ui=True)
    def sidebar(self) -> None:
        # ---------------- Sidebar ----------------
        with st.sidebar:
            st.title("🗄️ Database Connection")

            # Database Dropdown
            selected_db = st.selectbox(
                "Choose a Database Type",
                [
                    DatabaseType.SQLITE.value.lower(),
                    DatabaseType.POSTGRES.value.lower(),
                ],
                format_func=lambda db: f"🗄️ {db}",
                disabled=(st.secrets["dropdown"]["is_disabled"]).lower() == "true",
            )

            # Load the database config
            self.config = {
                selected_db: Helper.get_database_config(DatabaseType(selected_db))
            }

            # ❌ Prevent duplicate file creation on refresh
            if selected_db == DatabaseType.SQLITE.value.lower():
                uploaded_db = st.file_uploader("Select your .db file", type=["db"])

                if uploaded_db and not st.session_state.db_uploaded:
                    save_dir = "Data/DBs"
                    os.makedirs(save_dir, exist_ok=True)

                    import re
                    filename = str(uploaded_db.name).replace(".db", "").lower()
                    filename = filename.replace(" ", "_")
                    # keep only unicode letters, numbers, underscore and hyphen
                    filename = "".join(
                        c for c in filename
                        if unicodedata.category(c)[0] in ("L", "N") or c in "_-"
                    )
                    if not filename:
                        filename = "database"

                    self.unique_suffix = str(uuid.uuid4()).replace("-", "")
                    db_name = f"{filename}_{self.unique_suffix}"

                    save_path = os.path.join(save_dir, f"{db_name}.db")
                    Helper.save_db_file(save_path, uploaded_db)

                    st.session_state.db_name = db_name
                    st.session_state.db_uploaded = True

                    st.success("✅ File uploaded successfully!")

                if st.session_state.db_uploaded:
                    self.config[selected_db]["dbname"] = st.session_state.db_name
            else:
                st.session_state.db_uploaded = True
                st.session_state.db_name = self.config[selected_db]["dbname"]

            self.connect_database(selected_db)

            # ---------------- Schema Tree View ----------------
            if st.session_state.get("connected") and st.session_state.get("schema"):
                self.db_schema_tree_view(st.session_state["schema"])

    @exception_handler(show_ui=True)
    def db_schema_tree_view(self, schema: dict) -> None:
        st.markdown("### 📂 Database Schema")
        schema = st.session_state["schema"]

        for table_name, col_info in schema.items():
            with st.expander(f"🗄️ {table_name}", expanded=False):
                logger.debug("Rendering schema tree view for {table_name}")
                columns = col_info.get("columns")
                for col in columns:
                    col_name = col.get("name")
                    col_type = col.get("type")
                    col_type = len(col_type.split(" ")) > 0 and col_type.replace(" ", "_") or col_type
                    
                    icon = (
                        DataTypeIconMap[col_type.upper()].value
                        if col_type.upper() in DataTypeIconMap.__members__
                        else DataTypeIconMap.DEFAULT.value
                    )

                    st.markdown(
                        f"- {icon} **{col_name}** <span style='opacity:0.6'>({col_type})</span>",
                        unsafe_allow_html=True,
                    )

    @exception_handler(show_ui=True)
    def connect_database(self, selected_db: str) -> None:
        if st.button("⚡ Connect"):
            if st.session_state.get("connected", False):
                st.sidebar.info("✅ Same DB already exists - using previously connected DB.")
                return
            
            if st.session_state.db_uploaded:
                try:
                    status = st.empty()

                    with st.spinner("⏳ Processing...."):
                        logger.info(f"Connecting to DB: {selected_db}")

                        self.db = DatabaseRepository(
                            selected_db,
                            self.config[selected_db],
                        )
                        self.vectorstore = VectorStoreRepository(
                            VectorStoreType.FAISS.value.lower()
                        )
                        self.llm = LLMProviderRepository(
                            LLMProviderType.GROQ.value.lower()
                        )
                        time.sleep(1)

                        st.session_state["db"] = self.db
                        st.session_state["vectorstore"] = self.vectorstore
                        st.session_state["llm"] = self.llm

                        status.info("Fetching schema...")
                        schema = self.db.obj.get_schema()
                        time.sleep(1)

                        schema_chunks = Helper.schema_to_text(schema)
                        if len(schema_chunks) == 0:
                            status.error("Schema chunks empty!")
                            raise ValueError("Schema chunks empty!")
                        time.sleep(1)
                        
                        status.info("Building vector index...")
                        ok = self.vectorstore.obj.build_index(schema_chunks)

                        if ok is None:
                            status.error("Index build failed!")
                            raise VectorstoreError("Index build failed.")

                        self.vectorstore.obj.save_index(
                            "schema_context_" + self.config[selected_db]["dbname"]
                        )
                        time.sleep(1)

                        logger.info("Vector index saved.")
                        status.info("Vector index built and saved.")
                        time.sleep(1)

                        status.success(f"✅ Connected to {selected_db}!")
                        status.empty()

                        # ✅ Prevent reconnection on refresh
                        st.session_state.connected = True

                        # Save schema into session state so sidebar can display it
                        st.session_state["schema"] = schema

                except Exception as e:
                    logger.exception("Database connection failed!")
                    raise DatabaseConnectionError(str(e))
            else:
                st.sidebar.warning("⚠️ Please upload database (.db) file.")

    @exception_handler(show_ui=True)
    def process_query_ui(self) -> None:
        # ---------------- Main Input ----------------
        st.markdown("### ❓ Ask a Question")
        question = st.text_input("💬 Enter your question:")

        if st.button("🚀 Process Query"):
            try:
                if "db" not in st.session_state:
                    st.warning("⚠️ Please connect the database.")
                    return

                if not question.strip():
                    st.warning("⚠️ Please enter a question.")
                    return

                with st.spinner("⏳ Processing your request...."):
                    status = st.empty()
                    db = st.session_state["db"]
                    vectorstore = st.session_state["vectorstore"]
                    llm = st.session_state["llm"]

                    # Retrieve schema context from FAISS
                    status.info("Retrieving schema context from vectorstore")
                    context = vectorstore.obj.retrieve(question, k=3)

                    logger.debug(f"Retrieved schema context: {context}")
                    schema_context = "\n".join(context)  # join chunks
                    time.sleep(1)

                    status.info("Generating SQL Query...")
                    prompt = llm.obj.create_prompt_template()

                    query = {"context": schema_context, "question": question}
                    sql_query = llm.obj.generate(prompt, query)
                    time.sleep(1)

                    if Helper.check_for_unsafe_keywords(sql_query):
                        st.error(f"⚠️ Invalid SQL Query: {sql_query}")
                        return

                    rows, columns = db.obj.read(sql_query)
                    df = pd.DataFrame(rows, columns=columns)
                    
                    status.empty()

                # ---------------- Output ----------------
                st.subheader("📝 Generated SQL Query")
                st.code(sql_query, language="sql")

                st.subheader("📊 Query Results")
                st.dataframe(df)

            except Exception as e:
                logger.exception("Query error!")
                st.error("❌ Unexpected error during query processing.")


if __name__ == "__main__":
    App().main()
