import os
import time
import streamlit as st
import pandas as pd

from Core.Enums.database import DatabaseType
from Core.Enums.llm_provider import LLMProviderType
from Core.Enums.vectorstore import VectorStoreType

from Core.Repository.database import DatabaseRepository
from Core.Repository.llm_provider import LLMProviderRepository
from Core.Repository.vectorstore import VectorStoreRepository

from Core.Utils.logger import Logger
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import (
    DatabaseConnectionError,
    LLMProviderError,
    QueryExecutionError,
    VectorstoreError,
)
from Core.Utils.helper import Helper

logger = Logger.get_logger()


class App:
    def __init__(self):
        self.db = None
        self.vectorstore = None
        self.llm = None

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

        self.header()
        self.sidebar()
        self.process_query_ui()

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

        st.write(
            "Select a database, connect, and ask questions in plain English language."
        )

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
                disabled=False,
            )

            # Load the database config
            self.config = {
                selected_db: Helper.get_database_config(DatabaseType(selected_db))
            }

            if selected_db == DatabaseType.SQLITE.value.lower():
                uploaded_db = st.sidebar.file_uploader(
                    "Select your .db file", type=["db"]
                )

                if uploaded_db:
                    save_dir = "Data/DBs"
                    filename = self.config[selected_db].get("dbname", "sqlite_data")
                    uploaded_db.name = (
                        filename if filename.endswith(".db") else f"{filename}.db"
                    )

                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, uploaded_db.name)
                    Helper.save_db_file(save_path, uploaded_db)

                    st.session_state.db_file_path = save_path
                    st.sidebar.success(f"✅ File uploaded successfully!")

            self.connect_database(selected_db)

    @exception_handler(show_ui=True)
    def connect_database(self, selected_db: str) -> None:
        # Connect button
        if st.button("⚡ Connect"):
            try:
                status = st.empty()

                with st.spinner("⏳ Processing...."):
                    logger.info(f"Connecting to database: {selected_db}")
                    status.info("Initializing the repositories")
                    self.db = DatabaseRepository(
                        selected_db,
                        self.config[selected_db],
                    )
                    self.vectorstore = VectorStoreRepository(
                        VectorStoreType.FAISS.value.lower()
                    )
                    self.llm = LLMProviderRepository(LLMProviderType.GROQ.value.lower())
                    time.sleep(1)

                    st.session_state["db_name"] = selected_db
                    st.session_state["db"] = self.db
                    st.session_state["vectorstore"] = self.vectorstore
                    st.session_state["llm"] = self.llm

                    # Get schema context
                    db = st.session_state["db"]
                    vectorstore = st.session_state["vectorstore"]
                    llm = st.session_state["llm"]

                    status.info("Getting database schema context")
                    schema = db.obj.get_schema()

                    logger.debug(f"Schema retrieved: {str(schema)}")
                    time.sleep(1)

                    # Convert the schema to text
                    schema_chunks = Helper.schema_to_text(schema)
                    
                    if len(schema_chunks) == 0:
                        status.empty()
                        logger.exception(f"Schema Chunks Found: {schema_chunks}")
                        raise ValueError(f"Schema Chunks Found: {schema_chunks}")

                    # Saving Schema Context into Vectorstore
                    status.info("Saving schema context into vectorstore")
                    is_index_build = vectorstore.obj.build_index(schema_chunks)
                    if is_index_build is None: 
                        status.empty()
                        logger.exception(f"Schema Chunks Found: {schema_chunks}")
                        raise VectorstoreError("Schema context build failed.")
                    
                    vectorstore.obj.save_index("schema_store")

                    logger.info("Schema context saved into vectorstore")
                    time.sleep(1)

                    status.success(f"✅ Connected to {selected_db}!")
                    status.empty()

            except Exception as e:
                logger.exception("Database connection failed!")
                raise DatabaseConnectionError(str(e))

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

                    # Create prompt
                    status.info("Creating prompt")
                    prompt = llm.obj.create_prompt_template()
                    time.sleep(1)

                    # Generate SQL Query
                    status.info("Generating SQL query")
                    query = {
                        "context": schema_context,
                        "question": question,
                    }
                    sql_query = llm.obj.generate(prompt, query)

                    logger.info(f"Generated SQL query: {sql_query}")
                    time.sleep(1)

                    # Check for unsafe keywords
                    is_unsafe_keyword = Helper.check_for_unsafe_keywords(sql_query)
                    if is_unsafe_keyword:
                        logger.error(f"Invalid SQL Query: {sql_query}")
                        st.error(f"⚠️ Invalid SQL Query: {sql_query}")
                        return 
                    # Execute SQL query
                    rows, columns = db.obj.read(sql_query)
                    df = pd.DataFrame(rows, columns=columns)

                # ---------------- Output ----------------
                st.subheader("📝 Generated SQL Query")
                st.code(sql_query, language="sql")

                st.subheader("📊 Query Results")
                st.dataframe(df)

                status.empty()

            except QueryExecutionError as e:
                logger.error(f"Query execution failed: {e.message}")
                st.error(f"⚠️ Query execution failed: {e.message}")
            except VectorstoreError as e:
                logger.error(f"Vector store error: {e.message}")
                st.error(f"⚠️ Vector store Error: {e.message}")
            except LLMProviderError as e:
                logger.error(f"LLM provider error: {e.message}")
                st.error(f"⚠️ LLM Provider Error: {e.message}")
            except Exception as e:
                logger.exception("Unexpected error during query processing")
                st.error("❌ Unexpected error occurred while processing your query.")


if __name__ == "__main__":
    App().main()
