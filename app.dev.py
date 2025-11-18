from Core.Enums.database import DatabaseType
from Core.Enums.llm_provider import LLMProviderType
from Core.Enums.vectorstore import VectorStoreType

from Core.Repository.database import DatabaseRepository
from Core.Repository.llm_provider import LLMProviderRepository
from Core.Repository.vectorstore import VectorStoreRepository

import streamlit as st

from Core.Utils.helper import Helper


class App:
    def __init__(self):
        # Load the database config
        db_type = DatabaseType.POSTGRES.value.lower()
        self.config = {
            db_type: Helper.get_database_config(DatabaseType(db_type))
        }
        self.db = None
        self.vectorstore = None
        self.llm = None
        self.db_type = db_type

    def test(self):
        # Initialize the repositories
        self.db = DatabaseRepository(
            self.db_type,
            self.config[self.db_type],
        )
        self.vectorstore = VectorStoreRepository(VectorStoreType.FAISS.value.lower())
        self.llm = LLMProviderRepository(LLMProviderType.GROQ.value.lower())

        # Create dummy data
        # Helper.create_dummy_data(self.db)

        schema = self.db.obj.get_schema()

        # Convert the schema to text
        schema_chunks = Helper.schema_to_text(schema)

        self.vectorstore.obj.build_index(schema_chunks)
        self.vectorstore.obj.save_index("schema_context_" + self.config[self.db_type]["dbname"])
        self.vectorstore.obj.load_index("schema_context_" + self.config[self.db_type]["dbname"])

        # User question
        user_query = "Get the pages containing word 'graphical'"

        # Retrieve schema context from FAISS
        context = self.vectorstore.obj.retrieve(user_query, k=3)
        schema_context = "\n".join(context)  # join chunks

        # Create prompt
        prompt_template = self.llm.obj.create_prompt_template()

        # Generate SQL using Groq Llama
        query = {
            "context": schema_context,
            "question": user_query,
        }

        sql_query = self.llm.obj.generate(prompt_template, query)

        print(f"SQL Query: {sql_query}")

        # Check for unsafe keywords
        is_validate = Helper.check_for_unsafe_keywords(sql_query)

        if not is_validate:
            # Execute the SQL query
            rows, columns = self.db.obj.read(sql_query)
            print(rows, columns)


if __name__ == "__main__":
    App().test()
