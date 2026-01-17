import os
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

class VectorSearch:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB with persistent storage"""
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="document_collection",
            metadata={"hnsw:space": "cosine"},
            embedding_function=OpenAIEmbeddingFunction(
                model_name="text-embedding-3-small"
            )
        )   
        
        print(f"ChromaDB initialized with {self.collection.count()} documents")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]] = None, ids: List[str] = None):
        """Add documents to the vector database"""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        # Add to ChromaDB
        self.collection.add(
            documents=texts,
            metadatas=metadatas if metadatas else [{}] * len(texts),
            ids=ids
        )
        
        print(f"Added {len(texts)} documents to the database")
    
    def search_similar_ads(self, query: str, top_k: int = 5) -> str:
        """
        Search for similar product ads based on query
        Returns formatted string of results
        Args:
            query (str): The search query string.
            top_k (int): The number of top results to return.
        """
         
        # Search in ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results
        if not results['documents'] or not results['documents'][0]:
            return "No matching products found."
        
        formatted_results = []
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            formatted_results.append(f"{i+1}. {doc}")
            if metadata:
                formatted_results.append(f"   Metadata: {metadata}")
        
        return "\n".join(formatted_results)
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.client.delete_collection("product_ads")
        print("Collection deleted")
    
    def get_collection_info(self):
        """Get information about the collection"""
        return {
            "count": self.collection.count(),
            "name": self.collection.name,
            "metadata": self.collection.metadata
        }
