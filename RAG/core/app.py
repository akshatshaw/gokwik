"""
Streamlit UI for Document-Based Q&A System
"""

import os
import streamlit as st
from qa_system import QASystem
from document_processor import DocumentProcessor
# from config import validate_api_key
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def initialize_session_state():
    """Initialize session state variables."""
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "qa_system" not in st.session_state:
        st.session_state.qa_system = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "documents_loaded" not in st.session_state:
        st.session_state.documents_loaded = False
    if "uploaded_files_processed" not in st.session_state:
        st.session_state.uploaded_files_processed = False


def load_documents(api_key: str):
    """Load and process documents into vector store."""
    try:
        with st.spinner("Loading and processing documents..."):
            processor = DocumentProcessor()
            
            # Load documents
            docs = processor.load_documents()
            st.success(f"✅ Loaded {len(docs)} documents from folder")
            
            # Split documents
            split_docs = processor.split_documents(docs)
            st.info(f"📄 Split into {len(split_docs)} chunks")
            
            # Create vector store
            vector_store = processor.create_vector_store(split_docs, api_key)
            st.session_state.vector_store = vector_store
            
            # Initialize QA system
            st.session_state.qa_system = QASystem(vector_store, api_key)
            st.session_state.documents_loaded = True
            
            st.success("✅ Documents loaded successfully! You can now ask questions.")
            
    except Exception as e:
        st.error(f"❌ Error loading documents: {str(e)}")
        return False
    
    return True


def load_uploaded_documents(api_key: str, uploaded_files):
    """Load and process uploaded documents."""
    try:
        with st.spinner("Processing uploaded files..."):
            processor = DocumentProcessor()
            
            # Load uploaded files
            docs = processor.load_uploaded_files(uploaded_files)
            if not docs:
                st.error("❌ No documents could be loaded from uploaded files")
                return False
            
            st.success(f"✅ Loaded {len(docs)} documents from uploads")
            
            # Split documents
            split_docs = processor.split_documents(docs)
            st.info(f"📄 Split into {len(split_docs)} chunks")
            
            # Create vector store
            vector_store = processor.create_vector_store(split_docs, api_key)
            st.session_state.vector_store = vector_store
            
            # Initialize QA system
            st.session_state.qa_system = QASystem(vector_store, api_key)
            st.session_state.documents_loaded = True
            st.session_state.uploaded_files_processed = True
            
            st.success("✅ Uploaded documents processed! You can now ask questions.")
            
    except Exception as e:
        st.error(f"❌ Error processing uploads: {str(e)}")
        return False
    
    return True


def display_message(role: str, content: str, sources: list = None):
    """Display a chat message with optional sources."""
    with st.chat_message(role):
        st.markdown(content)
        
        if sources:
            with st.expander("📚 View Sources"):
                for i, source in enumerate(sources, 1):
                    file_name = os.path.basename(source['file'])
                    st.markdown(f"**Source {i}: {file_name}**")
                    st.text(source['content'])
                    st.divider()


def main():
    st.set_page_config(
        page_title="Document Q&A Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Document-Based Q&A Agent")
    st.markdown("Ask questions about your documents and get grounded answers with sources!")
    
    initialize_session_state()
    
    # Sidebar for configuration
    with st.sidebar:
         
        st.divider()
        
        st.header("📁 Document Management")
        
        # Tab for folder vs upload
        doc_source = st.radio(
            "Choose document source:",
            ["Load from folder", "Upload files"],
            horizontal=True
        )
        
        if doc_source == "Load from folder":
            st.info("Place your documents in the `documents/` folder")
            
            if st.button("🔄 Load Documents from Folder"):
                load_documents(api_key)
        else:
            st.info("Upload PDF, DOCX, or TXT files")
            
            uploaded_files = st.file_uploader(
                "Choose files",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key="file_uploader"
            )
            
            if uploaded_files and st.button("📤 Process Uploaded Files" ):
                load_uploaded_documents(api_key, uploaded_files)
        
        if st.session_state.documents_loaded:
            st.success("✅ Documents loaded")
        
        st.divider()
        
        st.header("ℹ️ About")
        st.markdown("""
        This AI agent answers questions using only the information from your documents.
        
        **Features:**
        - 🔍 Semantic search through documents
        - 📚 Source citations for transparency
        - 🚫 Avoids hallucination
        - ⚡ Fast retrieval with vector embeddings
        - 💬 Conversational memory
        - 📄 Supports PDF, DOCX, TXT files
        """)
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            if st.session_state.qa_system:
                st.session_state.qa_system.clear_history()
            st.rerun()
    
    # Main chat interface
    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started")
        st.stop()
    
    if not st.session_state.documents_loaded:
        st.info("👈 Click 'Load Documents' in the sidebar to start")
        st.stop()
    
    # Display chat history
    for message in st.session_state.messages:
        display_message(
            message["role"],
            message["content"],
            message.get("sources")
        )
    
    # Chat input
    if question := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        display_message("user", question)
        
        # Get answer from QA system
        try:
            with st.spinner("Searching documents..."):
                result = st.session_state.qa_system.ask(question)
                
            answer = result["answer"]
            sources = result["sources"]
            
            # Add assistant message to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
            display_message("assistant", answer, sources)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
