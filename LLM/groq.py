from typing import Any, Dict
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

from Core.Base.llm_provider import BaseLLMProvider
from Core.Enums.llm_provider import LLMProviderType
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import LLMProviderError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


class GroqLLM(BaseLLMProvider):
    llm_type = LLMProviderType.GROQ.value.lower()

    @exception_handler(show_ui=True)
    def __init__(self, config: Dict):
        if not hasattr(self, "initialized"):
            self.config = config

            if not self.config.get("api_key"):
                raise LLMProviderError("❌ GROQ API KEY is missing.")

            logger.info(
                "🔑 Initializing Groq LLM with model=%s", self.config.get("model")
            )

            try:
                self.llm = ChatGroq(
                    model=self.config.get("model"),
                    groq_api_key=self.config.get("api_key"),
                    temperature=self.config.get("temperature", 0.0),
                    max_tokens=self.config.get("max_tokens", 200),
                )
            except Exception as e:
                raise LLMProviderError(f"Groq LLM initialization failed: {str(e)}")

            self.initialized = True
            logger.info("✅ Groq LLM initialized successfully.")

    @exception_handler(show_ui=True)
    def create_prompt_template(self) -> Any:
        try:
            logger.info("📝 Creating prompt template for Groq LLM.")
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""
                    You are an expert in converting English questions into SQL queries.

                    ### Database Schema:
                    {context}

                    ### Instructions
                    - Convert the given English question into a valid SQL query.
                    - Use only the provided table and columns.
                    - Provide the proper alias name to the columns.
                    - Do not add explanations, comments, preamble, or extra text.
                    - Do not include the word "sql" anywhere.
                    - Do not wrap the query in backticks (```).
                    - Only return the SQL query.

                    ### User Question
                    {question}
                """,
            )
            logger.info("✅ Prompt template created successfully.")
            return prompt_template
        except Exception as e:
            raise LLMProviderError(f"Prompt template creation failed: {str(e)}")

    @exception_handler(show_ui=True)
    def generate(self, prompt_template: PromptTemplate, query: Dict[str, Any]) -> str:
        try:
            logger.info(
                "⚡ Generating SQL query using Groq LLM for question: %s",
                query.get("question"),
            )
            chain = prompt_template | self.llm
            response = chain.invoke(query)
            sql_query = response.content.strip()
            logger.info("✅ SQL query generated successfully.")
            return sql_query
        except Exception as e:
            raise LLMProviderError(f"SQL generation failed: {str(e)}")
