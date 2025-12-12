import os
import streamlit as st

class AppConfig:
    REQUIRED_ENV_VARS = [
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_MODEL"
    ]

    @staticmethod
    def validate() -> bool:
        missing = [v for v in AppConfig.REQUIRED_ENV_VARS if not os.getenv(v)]
        if missing:
            st.error("❌ Missing Environment Variables")
            st.write("Please add these to your `.env` file:")
            for var in missing:
                st.write(f"- `{var}`")
            return False
        return True

    @staticmethod
    def setup_page():
        st.set_page_config(
            page_title="Contract Analyzer",
            page_icon="📄",
            layout="wide"
        )