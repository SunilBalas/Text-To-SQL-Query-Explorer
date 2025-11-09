from Core.Factory.llm_provider import LLMProviderFactory

import streamlit as st


class LLMProviderRepository:
    def __init__(self, llm_type: str):
        self.config = {
            llm_type: {
                "type": st.secrets[llm_type]["type"],
                "model": st.secrets[llm_type]["model"],
                "api_key": st.secrets[llm_type]["api_key"],
                "temperature": st.secrets[llm_type]["temperature"],
                "max_tokens": st.secrets[llm_type]["max_tokens"],
            }
        }
        self.obj = LLMProviderFactory.get_llm_provider(
            llm_type, self.config[llm_type]
        )
