import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.vector_search_clean import VectorSearch


class DocumentLoader:
    def __init__(self, vector_db: VectorSearch = None):
        """Initialize document loader with vector database"""
        self.vector_db = vector_db if vector_db else VectorSearch()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_file(self, file_path: str) -> List:
        """Load a file based on its extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_extension in ['.docx', '.doc']:
            loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        documents = loader.load()
        return documents
    
    def split_documents(self, documents: List) -> List:
        """Split documents into chunks"""
        chunks = self.text_splitter.split_documents(documents)
        return chunks
    
    def process_and_store(self, file_path: str):
        """Load, split, and store a document in the vector database"""
        print(f"Processing file: {file_path}")
        
        # Load document
        documents = self.load_file(file_path)
        print(f"Loaded {len(documents)} documents")
        
        # Split into chunks
        chunks = self.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        
        # Prepare data for vector DB
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [
            {
                "source": file_path,
                "page": chunk.metadata.get("page", 0),
                "chunk_id": i
            }
            for i, chunk in enumerate(chunks)
        ]
        ids = [f"{os.path.basename(file_path)}_chunk_{i}" for i in range(len(chunks))]
        
        # Store in vector database
        self.vector_db.add_documents(texts=texts, metadatas=metadatas, ids=ids)
        
        print(f"Successfully stored {len(chunks)} chunks in vector database")
        return len(chunks)
    
    def process_directory(self, directory_path: str):
        """Process all supported files in a directory"""
        supported_extensions = ['.pdf', '.txt', '.docx', '.doc']
        total_chunks = 0
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            if os.path.isfile(file_path):
                file_extension = os.path.splitext(filename)[1].lower()
                
                if file_extension in supported_extensions:
                    try:
                        chunks = self.process_and_store(file_path)
                        total_chunks += chunks
                    except Exception as e:
                        print(f"Error processing {filename}: {str(e)}")
        
        print(f"\nTotal chunks stored: {total_chunks}")
        return total_chunks


if __name__ == "__main__":
    # Example usage
    loader = DocumentLoader()
    
    # Process a single file
    # loader.process_and_store("path/to/your/document.pdf")
    
    # Or process all files in a directory
    # loader.process_directory("path/to/your/documents")
    
    print("\nVector DB Info:", loader.vector_db.get_collection_info())
