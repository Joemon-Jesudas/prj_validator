from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import json
import os

from config import AppConfig
from services.azure_clients import AzureClientManager
from services.document_extractor import DocumentExtractor
from services.contract_analyzer import ContractAnalyzer
from utils.excel_writer import convert_validation_to_excel

app = FastAPI(title="Document Validator System")

# Initialize Azure clients
try:
    azure = AzureClientManager()
    doc_client = getattr(azure, "doc_client", None)
    openai_client = getattr(azure, "openai_client", None)
    if doc_client is None or openai_client is None:
        raise RuntimeError("Azure clients not fully initialized. Check environment variables.")
except Exception as e:
    raise HTTPException(status_code=500, detail="Failed to initialize Azure clients.")

extractor = DocumentExtractor(doc_client)
analyzer = ContractAnalyzer(openai_client)

@app.post("/analyze/")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Read PDF bytes
        pdf_content = await file.read()

        # Extract text
        full_text, page_count, extraction_time = extractor.extract_text(pdf_content)

        # Analyze contract
        result_json, analysis_time, usage_stats = analyzer.analyze(full_text)

        response = {
            "file_name": file.filename,
            "extraction_time": extraction_time,
            "page_count": page_count,
            "analysis_time": analysis_time,
            "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": result_json,
            "usage_stats": usage_stats
        }

        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
