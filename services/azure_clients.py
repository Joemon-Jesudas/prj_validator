import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from openai import AzureOpenAI

load_dotenv()

class AzureClientManager:
    """
    Initializes and exposes Azure Document Intelligence and Azure OpenAI clients.
    """

    def __init__(self):
        doc_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        doc_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        openai_key = os.getenv("AZURE_OPENAI_API_KEY")
        openai_version = os.getenv("AZURE_OPENAI_API_VERSION")

        if not all([doc_endpoint, doc_key, openai_endpoint, openai_key, openai_version]):
            # Intentionally not raising here — the app will show env errors via AppConfig.validate()
            return

        self.doc_client = DocumentIntelligenceClient(
            endpoint=doc_endpoint,
            credential=AzureKeyCredential(doc_key)
        )

        # The AzureOpenAI client in this example expects the constructor args below
        # (This mirrors the usage from your original code snippet).
        self.openai_client = AzureOpenAI(
            api_version=openai_version,
            azure_endpoint=openai_endpoint,
            api_key=openai_key
        )
