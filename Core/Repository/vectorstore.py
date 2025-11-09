from Core.Factory.vectorstore import VectorStoreFactory

import streamlit as st


class VectorStoreRepository:
    def __init__(self, vectorstore_type: str):
        self.config = {
            vectorstore_type: {   
                "type": st.secrets[vectorstore_type]["type"],
                "model": st.secrets[vectorstore_type]["model"],
            }
        }
        self.obj = VectorStoreFactory.get_vectorstore(vectorstore_type, self.config[vectorstore_type])
