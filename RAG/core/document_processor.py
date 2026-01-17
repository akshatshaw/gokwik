"""
Document loader and vector store utilities for RAG system.
"""

import os
import tempfile
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader, 
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


class DocumentProcessor:
    """Handles document loading and processing for the RAG system."""
    
    def __init__(self, documents_path: str = "./documents"):
        self.documents_path = documents_path
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def load_documents(self) -> List[Document]:
        """Load all documents from the documents directory."""
        if not os.path.exists(self.documents_path):
            raise FileNotFoundError(f"Documents directory not found: {self.documents_path}")
        
        all_documents = []
        
        # Load text files
        txt_loader = DirectoryLoader(
            self.documents_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=False,
        )
        try:
            all_documents.extend(txt_loader.load())
        except:
            pass
        
        # Load PDF files
        pdf_files = []
        for root, dirs, files in os.walk(self.documents_path):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(pdf_file)
                all_documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {pdf_file}: {e}")
        
        # Load DOCX files
        docx_files = []
        for root, dirs, files in os.walk(self.documents_path):
            for file in files:
                if file.endswith('.docx'):
                    docx_files.append(os.path.join(root, file))
        
        for docx_file in docx_files:
            try:
                loader = Docx2txtLoader(docx_file)
                all_documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {docx_file}: {e}")
        
        if not all_documents:
            raise ValueError("No documents found in the directory")
        
        return all_documents
    
    def load_uploaded_files(self, uploaded_files) -> List[Document]:
        """Load documents from uploaded files."""
        documents = []
        
        for uploaded_file in uploaded_files:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Determine loader based on file extension
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                
                if file_extension == '.pdf':
                    loader = PyPDFLoader(tmp_path)
                elif file_extension == '.docx':
                    loader = Docx2txtLoader(tmp_path)
                elif file_extension == '.txt':
                    loader = TextLoader(tmp_path)
                else:
                    # Skip unsupported file types
                    continue
                
                docs = loader.load()
                # Add filename to metadata
                for doc in docs:
                    doc.metadata['source'] = uploaded_file.name
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading {uploaded_file.name}: {e}")
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks."""
        return self.text_splitter.split_documents(documents)
    
    def create_vector_store(self, documents: List[Document], api_key: str) -> Chroma:
        """Create a vector store from documents."""
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        
        return vector_store
    
    def load_vector_store(self, api_key: str) -> Chroma:
        """Load existing vector store."""
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        
        vector_store = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
        vector_store.persist()
        return vector_store
