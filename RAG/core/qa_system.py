"""
Q&A Chain implementation using LangChain.
"""
import os
from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
load_dotenv()


class QASystem:
    """Handles question answering using RAG."""
    
    def __init__(self, vector_store: Chroma, api_key: str, model: str = "gpt-3.5-turbo"):
        self.vector_store = vector_store
        self.api_key = os.getenv("OPENAI_API_KEY") 
        self.model = model
        self.retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        self.chat_history = []
        
        # Create a custom prompt with chat history support
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions based ONLY on the provided context.

IMPORTANT RULES:
1. Only use information from the context below to answer questions
2. If the answer cannot be found in the context, respond with: "I don't have enough information in the documents to answer this question."
3. Always cite which document the information comes from
4. Do not make up or infer information beyond what's explicitly stated
5. Be concise and direct in your answers
6. You can refer to previous conversation when relevant

Context:
{context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.5,
            openai_api_key=self.api_key
        )
    
    def format_docs(self, docs):
        """Format documents for context."""
        return "\n\n".join([doc.page_content for doc in docs])
    
    def ask(self, question: str) -> Dict:
        """Ask a question and get an answer with sources."""
        # Retrieve relevant documents
        docs = self.retriever.invoke(question)
        
        # Create the chain
        chain = (
            {
                "context": lambda x: self.format_docs(docs),
                "chat_history": lambda x: self.chat_history,
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Get the answer
        answer = chain.invoke(question)
        
        # Update chat history
        self.chat_history.append(HumanMessage(content=question))
        self.chat_history.append(AIMessage(content=answer))
        
        # Keep only last 10 exchanges (20 messages)
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
        
        # Format the response
        response = {
            "answer": answer,
            "sources": []
        }
        
        # Extract source information
        for doc in docs:
            source_info = {
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "file": doc.metadata.get("source", "Unknown"),
            }
            response["sources"].append(source_info)
        
        return response
    
    def clear_history(self):
        """Clear the conversation history."""
        self.chat_history = []
