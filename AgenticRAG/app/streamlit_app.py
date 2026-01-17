import streamlit as st
import asyncio
import sys
import os
import tempfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from QA_Bot.agent import generate_response, call_agent_async
from utils.document_loader import DocumentLoader
from utils.vector_search_clean import VectorSearch

vectordb = VectorSearch()

st.set_page_config(
    page_title="Document Chat Agent",
    page_icon="📚",
    layout="centered"
)

st.title("📚 Document Chat Agent")
st.caption("Ask questions about your documents")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about your documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Get response from agent
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(call_agent_async(prompt))
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar
with st.sidebar:
    st.header("📁 Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Upload PDF, TXT, or DOCX files",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        help="Upload documents to chat with the AI agent"
    )
    
    if uploaded_files:
        if st.button("Process Documents", type="primary"):
            with st.spinner("Processing documents..."):
                try:
                    # Initialize document loader
                    doc_loader = DocumentLoader(vector_db=vectordb)
                    total_chunks = 0
                    
                    for uploaded_file in uploaded_files:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        try:
                            # Process the file
                            chunks = doc_loader.process_and_store(tmp_file_path)
                            total_chunks += chunks
                            st.success(f"✅ {uploaded_file.name}: {chunks} chunks")
                        except Exception as e:
                            st.error(f"❌ {uploaded_file.name}: {str(e)}")
                        finally:
                            # Clean up temp file
                            if os.path.exists(tmp_file_path):
                                os.unlink(tmp_file_path)
                    
                    st.success(f"🎉 Total {total_chunks} chunks added to database!")
                    
                    # Show database info
                    db_info = doc_loader.vector_db.get_collection_info()
                    st.info(f"📊 Total documents in DB: {db_info['count']}")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.divider()
    
    st.header("About")
    st.info(
        "This is a document chat agent powered by AI. "
        "Ask questions about your uploaded documents and get accurate answers!"
    )
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        vectordb.delete_collection()
        st.rerun()
