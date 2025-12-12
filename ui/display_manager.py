import streamlit as st
from typing import Any, Dict
from utils.validators import get_status_style

class DisplayManager:
    """All UI rendering logic for displaying extraction results."""

    @staticmethod
    def show_file_info(uploaded_file) -> None:
        size_mb = uploaded_file.size / (1024 * 1024)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{size_mb:.2f} MB")
        if size_mb > 50:
            st.warning("⚠️ File size exceeds 50 MB. Processing may take longer.")

    @staticmethod
    def show_processing_stats(extraction_time: float, analysis_time: float, page_count: int, processed_time: str,usage_stats: str) -> None:
        st.sidebar.subheader("📊 Processing Statistics")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Extraction Time", f"{extraction_time:.2f}s")
        with col2:
            st.metric("Analysis Time", f"{analysis_time:.2f}s")

        st.sidebar.metric("Pages Processed", page_count)
        st.sidebar.caption(f"Processed: {processed_time}")

        # st.sidebar.subheader("🧮 Token Usage")
        # col1, col2, col3 = st.sidebar.columns(3)
        # with col1:
        #     st.metric("Input Tokens",usage_stats.get("prompt_tokens",0))
        # with col2:
        #     st.metric("Output Tokens",usage_stats.get("completion_tokens",0))
        # with col3:
        #     st.metric("Total Tokens",usage_stats.get("total_tokens",0))

    @staticmethod
    def show_results(result: Dict[str, Any]) -> None:
        st.divider()
        st.subheader("📊 Extraction Results")

        # Template Classification
        with st.expander("📋 Template Classification", expanded=True):
            template = result.get("template_classification", {})
            st.write(f"**Type:** {template.get('type', 'N/A')}")
            keywords = template.get("keywords_found", [])
            st.write(f"**Keywords:** {', '.join(keywords) if keywords else 'None'}")
            st.write(f"**Confidence:** {template.get('confidence', 'N/A')}")

        # Party Information
        with st.expander("🏢 Party Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                allianz = result.get("allianz_details", {})
                st.write("**Allianz Details**")
                st.write(f"Name: {allianz.get('name', 'N/A')}")
                st.write(f"Address: {allianz.get('address', 'N/A')}")
                status = allianz.get("validation_status", "N/A")
                st.markdown(f"Status: <span class='{get_status_style(status)}'>{status}</span>", unsafe_allow_html=True)
            with col2:
                supplier = result.get("supplier_details", {})
                st.write("**Supplier Details**")
                st.write(f"Name: {supplier.get('name', 'N/A')}")
                st.write(f"Address: {supplier.get('address', 'N/A')}")
                status = supplier.get("validation_status", "N/A")
                st.markdown(f"Status: <span class='{get_status_style(status)}'>{status}</span>", unsafe_allow_html=True)
        # Customer Contact
        with st.expander("👤 Customer Contact", expanded=True):
            customer = result.get("customer_contact", {})
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Surname:** {customer.get('Surname', 'N/A')}")
                st.write(f"**First Name:** {customer.get('First name', 'N/A')}")
            
            with col2:
                st.write(f"**Telephone:** {customer.get('Telephone number', 'N/A')}")
                st.write(f"**Email:** {customer.get('e-mail address', 'N/A')}")
            
            status = customer.get("validation_status", "N/A")
            st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                    unsafe_allow_html=True)
        
        # Contractor's Project Manager
        with st.expander("👨‍💼 Contractor's Project Manager", expanded=True):
            contractor = result.get("contractor_project_manager", {})
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Surname:** {contractor.get('Surname', 'N/A')}")
                st.write(f"**First Name:** {contractor.get('First name', 'N/A')}")
            
            with col2:
                st.write(f"**Telephone:** {contractor.get('Telephone number', 'N/A')}")
                st.write(f"**Email:** {contractor.get('e-mail address', 'N/A')}")
            
            status = contractor.get("validation_status", "N/A")
            st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                    unsafe_allow_html=True)
        
        # Place of Performance
        with st.expander("📍 Place of Performance", expanded=True):
            place = result.get("place_of_performance", {})
            st.write(f"**Selected Option:** {place.get('type', 'N/A')}")
            details = place.get('details', 'N/A')
            if isinstance(details, dict):
                # Render as table
                details_table = "| Field | Value |\n|-------|-------|\n"
                for k, v in details.items():
                    details_table += f"| {k} | {v} |\n"
                st.markdown(details_table)
            elif isinstance(details, str):
                st.write(f"**Details:** {details}")
            else:
                st.write("**Details:** N/A")

        
        # Subcontractor Details
        with st.expander("🤝 Subcontractor Details", expanded=True):
            subcontractor = result.get("subcontractor_details", {})
            present = subcontractor.get("present", False)
            st.write(f"**Present:** {'Yes' if present else 'No'}")
            if present:
                st.write(f"**Details:** {subcontractor.get('details', 'N/A')}")

        with st.expander("💰 Remuneration Details", expanded=True):
            remuneration = result.get("remuneration_details", {})
        
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("**Marked Options:**")
                for option in remuneration.get("marked_options", []):
                    st.write(f"- {option.get('option', 'N/A')}")
                    if option.get('amount') != 'N/A' and option.get('amount') != 'Missing':
                        st.write(f"  Amount: {option.get('amount', 'N/A')} {option.get('currency', 'N/A')}")
                    if option.get('rate_card_status') != 'N/A':
                        st.write(f"  Rate Card: {option.get('rate_card_status', 'N/A')}")
        
            with col2:
                status = remuneration.get("validation_status", "N/A")
                st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                        unsafe_allow_html=True)
            
            st.info(remuneration.get("validation_reason", "No details"))

        # Invoicing
        with st.expander("📧 Invoicing", expanded=True):
            invoicing = result.get("invoicing", {})
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("**Marked Options:**")
                for option in invoicing.get("marked_options", []):
                    st.write(f"- {option.get('option', 'N/A')}")
                    if option.get('milestone_details') and option.get('milestone_details') != 'N/A':
                        st.write(f"  Milestones: {option.get('milestone_details', 'N/A')}")
            
            with col2:
                status = invoicing.get("validation_status", "N/A")
                st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                        unsafe_allow_html=True)
            
            st.write(f"**Cross-Validation:** {invoicing.get('cross_validation_with_remuneration', 'N/A')}")
            st.info(invoicing.get("validation_reason", "No details"))


            # VAT
        with st.expander("💶 VAT (Value Added Tax)", expanded=True):
            vat = result.get("vat", {})
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Marked Option:** {vat.get('marked_option', 'N/A')}")
                st.write(f"**Expected Option:** {vat.get('expected_option', 'N/A')}")
                st.write(f"**Supplier Name:** {vat.get('supplier_name', 'N/A')}")
            
            with col2:
                status = vat.get("validation_status", "N/A")
                st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                        unsafe_allow_html=True)
            
            st.info(vat.get("validation_reason", "No details"))

        # Invoice Address
        with st.expander("📮 Invoice Address", expanded=True):
            invoice = result.get("invoice_address", {})
            
            if invoice.get("address_present"):
                st.write(f"**Extracted Address:** {invoice.get('extracted_address', 'N/A')}")
                st.write(f"**Matched With:** {invoice.get('matched_address', 'None')}")
            
            status = invoice.get("validation_status", "N/A")
            st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                    unsafe_allow_html=True)
            st.info(invoice.get("validation_reason", "No details"))

        # Data Protection, Security, Outsourcing
        with st.expander("🔒 Data Protection, Information Security & Outsourcing", expanded=True):
            dps = result.get("data_protection_security_outsourcing", {})
            
            for category, label in [
                ("data_protection", "Data Protection"),
                ("information_security", "Information Security"),
                ("outsourcing", "Outsourcing")
            ]:
                st.write(f"**{label}:**")
                cat_data = dps.get(category, {})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"Marked: {cat_data.get('marked', 'N/A')}")
                with col2:
                    st.write(f"Document: {'Yes' if cat_data.get('document_included') else 'No'}")
                with col3:
                    status = cat_data.get("validation_status", "N/A")
                    st.markdown(f"<span class='{get_status_style(status)}'>{status}</span>", 
                            unsafe_allow_html=True)
                
                st.caption(cat_data.get("validation_reason", ""))
                st.divider()

        # Terms and Termination
        with st.expander("📅 Terms and Termination", expanded=True):
            terms = result.get("terms_and_termination", {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Start Date", terms.get("start_date", "Missing"))
            with col2:
                st.metric("End Date", terms.get("end_date", "Missing"))
            with col3:
                st.metric("Duration", terms.get("contract_duration", "N/A"))
            
            st.write(f"**Multiyear Contract:** {'Yes' if terms.get('is_multiyear') else 'No'}")
            
            status = terms.get("validation_status", "N/A")
            st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                    unsafe_allow_html=True)
            st.info(terms.get("validation_reason", "No details"))

        # Signature Verification
        with st.expander("✍️ Signature Verification", expanded=True):
            sig = result.get("signature_verification", {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Signatures", sig.get("total_signatures", 0))
            with col2:
                st.metric("Allianz", sig.get("allianz_signatures", 0))
            with col3:
                st.metric("Supplier", sig.get("supplier_signatures", 0))
            with col4:
                st.metric("Required", sig.get("required_signatures", 0))
            
            st.write(f"**GSP Approval Present:** {'Yes' if sig.get('gsp_approval_present') else 'No'}")
            st.write(f"**Applied Rules:** {', '.join(sig.get('applied_rules', []))}")
            
            status = sig.get("validation_status", "N/A")
            st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                    unsafe_allow_html=True)
            st.info(sig.get("validation_reason", "No details"))

        # Legal Clause Validation
        with st.expander("📅 Legal Clause Validation", expanded=True):
            legal_check = result.get("legal_clause_validation", {})
            status = legal_check.get("validation_status", "N/A")
            st.markdown(f"**Status:** <span class='{get_status_style(status)}'>{status}</span>", 
                    unsafe_allow_html=True)

            changes = legal_check.get("changes", {})
            sections = changes.get("sections", "No changes identified")
            clause_position = changes.get("clause_position", "N/A")
            words_changed = changes.get("words_changed", "N/A")

            st.markdown(f"**Sections:** {sections}")
            st.info(f"Clause Position: {clause_position}")
            st.info(f"Words Changed: {words_changed}")

        with st.expander("📄 Service Description Validation", expanded=True):
            service_check = result.get("service_description_validation", {})
            status_val = service_check.get("validation_status", "N/A")
            
            st.markdown(f"**Status:** <span class='{get_status_style(status_val)}'>{status_val}</span>", 
                    unsafe_allow_html=True)
            
            differences = service_check.get("modified_sections", [])
            if differences:
                st.subheader("Differences")
                for diff in differences:
                    section = diff.get("section", "N/A")
                    difference = diff.get("difference_summary", "N/A")
                    
                    st.markdown(f"**Section:** {section}")
                    st.text_area(f"Difference", value=difference, height=150)
            else:
                st.success("No differences found between contract and reference service description.")



        # Provide JSON viewer at the end
        with st.expander("📋 View Raw JSON", expanded=False):
            st.json(result)
