import os
import json
from datetime import datetime
import streamlit as st

from config import AppConfig
from services.azure_clients import AzureClientManager
from services.document_extractor import DocumentExtractor
from services.contract_analyzer import ContractAnalyzer
from services.service_description_validator import ServiceDescriptionValidator
from services.servicenow_client import ServiceNowClient
from ui.styles import Styles
from ui.display_manager import DisplayManager
from utils.excel_writer import convert_validation_to_excel


# -------------------------------------------------------
# MAIN APPLICATION
# -------------------------------------------------------
def main():

    # Page setup
    AppConfig.setup_page()
    Styles.load()

    st.markdown("""
        <div class="header-section">
            <h1>📄 ServiceNow Agreement Analyzer</h1>
            <p>Fetch an agreement by Request ID and run AI-powered contract analysis using Azure services.</p>
        </div>
    """, unsafe_allow_html=True)

    # Validate environment
    if not AppConfig.validate():
        st.stop()

    # Initialize Azure
    try:
        azure = AzureClientManager()
        doc_client = azure.doc_client
        openai_client = azure.openai_client
    except Exception as e:
        st.error("Failed to initialize Azure clients.")
        st.exception(e)
        st.stop()

    extractor = DocumentExtractor(doc_client)
    analyzer = ContractAnalyzer(openai_client)
    validator = ServiceDescriptionValidator(openai_client)

    # Sidebar
    with st.sidebar:
        st.sidebar.markdown(
            """
            <div style="padding-bottom: 12px;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Allianz.svg/2560px-Allianz.svg.png"
                width="160" style="padding:5px 0;" />
            </div>
            """,
            unsafe_allow_html=True
        )
        st.divider()
        st.header("ℹ️ App Info")
        st.info("Fetch documents from ServiceNow and analyze contracts using Azure Document Intelligence + Azure OpenAI.")
        st.divider()

    init_session_state()

    # -------------------------------------------------------
    # ServiceNow Input
    # -------------------------------------------------------
    st.subheader("🔑 Enter ServiceNow Request ID")

    request_id = st.text_input("Request ID (e.g., BUY0001009)", placeholder="BUY0001009")

    col1, col2 = st.columns(2)
    with col1:
        fetch_btn = st.button("🚀 Fetch & Analyze", use_container_width=True)
    with col2:
        clear_btn = st.button("🔄 Clear", use_container_width=True)

    if clear_btn:
        reset_state()
        st.experimental_rerun()

    if fetch_btn:
        try:
            if not request_id.strip():
                st.error("Request ID cannot be empty.")
                st.stop()

            sn = ServiceNowClient()

            # Fetch metadata
            st.info(f"🔍 Fetching ServiceNow record for: **{request_id}**")
            with st.spinner("Querying ServiceNow..."):
                raw, metadata = sn.get_record(request_id)

                if not raw:
                    st.error("No record found for this Request ID.")
                    st.stop()

                # Remove fields we do not want to show
                metadata.pop("requested_for", None)
                metadata.pop("requested_by", None)

                sys_id = metadata["sys_id"]
                st.session_state.servicenow_metadata = metadata

            # Download attachment
            with st.spinner("Downloading attached agreement..."):
                attachment = sn.download_attachment_bytes(sys_id)

                if not attachment:
                    st.error("No attachment found for this request.")
                    st.stop()

                pdf_bytes = attachment["bytes"]
                st.session_state.file_name = attachment["file_name"]

            # Run pipeline
            run_pipeline(pdf_bytes, extractor, analyzer, validator)

        except Exception as e:
            st.error("❌ Error processing ServiceNow document")
            with st.expander("View Error Details"):
                st.code(str(e))

    # -------------------------------------------------------
    # RESULTS
    # -------------------------------------------------------
    if st.session_state.processing_complete and st.session_state.result:

        # SN metadata UI
        if st.session_state.servicenow_metadata:
            render_servicenow_metadata(st.session_state.servicenow_metadata)

        # Azure stats
        DisplayManager.show_processing_stats(
            extraction_time=st.session_state.extraction_time,
            analysis_time=st.session_state.analysis_time,
            page_count=st.session_state.page_count,
            processed_time=st.session_state.processing_time,
            usage_stats=st.session_state.usage_stats
        )

        # Analysis results
        DisplayManager.show_results(st.session_state.result)

        # Downloads
        json_out = json.dumps(st.session_state.result, indent=2)
        excel_out = convert_validation_to_excel(st.session_state.result)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "⬇️ JSON Results",
                json_out,
                f"contract_analysis_{ts()}.json",
                "application/json",
                use_container_width=True
            )
        with c2:
            st.download_button(
                "⬇️ Text Results",
                json_out,
                f"contract_analysis_{ts()}.txt",
                "text/plain",
                use_container_width=True
            )
        with c3:
            st.download_button(
                "⬇️ Excel Report",
                excel_out,
                f"contract_validation_{ts()}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    st.divider()
    st.caption("📝 Contract Analyzer v2.3 — ServiceNow Edition")


# -------------------------------------------------------
# BEAUTIFUL SERVICENOW METADATA UI
# -------------------------------------------------------
def render_servicenow_metadata(md: dict):

    st.subheader("📌 ServiceNow Request Metadata")

    st.markdown("""
        <style>
        .sn-card {
            background: #eef4ff;
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 12px;
            border-left: 5px solid #0057b8;
        }
        .sn-label {
            font-weight: 600;
            color: #003f8c;
            font-size: 13px;
        }
        .sn-value {
            font-weight: 500;
            color: #111;
            font-size: 15px;
            margin-top: 2px;
        }
        </style>
    """, unsafe_allow_html=True)

    def card(label, value):
        st.markdown(
            f"""
            <div class="sn-card">
                <div class="sn-label">{label}</div>
                <div class="sn-value">{value if value else "—"}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # REQUEST DETAILS
    card("Request Number", md.get("request_number"))
    card("PR Requestor Number", md.get("pr_requestor_number"))
    card("PR Start Date", md.get("pr_start_date"))

    # Supplier
    st.markdown("### 🏢 Supplier")
    card("Supplier ID", md.get("supplier_id"))

    # Fieldglass
    st.markdown("### 📋 Fieldglass Checklist")
    card("Checklist ID", md.get("fieldglass_checklist_id"))
    card("Approval Date", md.get("fieldglass_checklist_approval_date"))

    # Remuneration
    st.markdown("### 💰 Remuneration")
    card("Remuneration Details", md.get("remuneration_details"))


# -------------------------------------------------------
# PROCESSING PIPELINE
# -------------------------------------------------------
def run_pipeline(pdf_bytes, extractor, analyzer, validator):
    status = st.empty()
    status.info("📖 Extracting text from PDF...")

    with st.spinner("Extracting..."):
        full_text, pages, t_extract = extractor.extract_text(pdf_bytes)
        service_md = extractor.extract_service_description(full_text)

    st.session_state.extraction_time = t_extract
    st.session_state.page_count = pages

    status.info("🤖 Running AI analysis...")
    with st.spinner("Analyzing contract..."):
        result_json, t_analysis, usage = analyzer.analyze(full_text)
        validation = validator.validate_service_description(service_md)

        result_json["service_description_validation"] = validation

        # Attach clean metadata
        if st.session_state.servicenow_metadata:
            result_json["servicenow_metadata"] = st.session_state.servicenow_metadata

    st.session_state.result = result_json
    st.session_state.analysis_time = t_analysis
    st.session_state.usage_stats = usage
    st.session_state.processing_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.processing_complete = True

    status.empty()
    st.success("Document processed successfully!")


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------
def init_session_state():
    if "processing_complete" not in st.session_state:
        reset_state()

def reset_state():
    st.session_state.processing_complete = False
    st.session_state.result = None
    st.session_state.file_name = None
    st.session_state.servicenow_metadata = None

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    main()
