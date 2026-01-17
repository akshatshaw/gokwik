import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

import os
from dotenv import load_dotenv

from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import FunctionTool, agent_tool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.models.lite_llm import LiteLlm
from opik.integrations.adk import OpikTracer
from google.genai import types
from typing import Optional, Dict, Any
import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_search_clean import VectorSearch
vs = VectorSearch()

os.environ["OPIK_WORKSPACE"] = "akshatshaw"
opik_tracer = OpikTracer(project_name="GoKwik")

search_tool = FunctionTool(func=vs.search_similar_ads)

load_dotenv()
AGENT_MODEL = LiteLlm(model="openai/gpt-4.1") 

# RAG agent (modified to work with rewritten queries)
root_agent = Agent(
    name="DocumentRAGAgent",
    model=AGENT_MODEL,
    description="Document-focused RAG agent that retrieves relevant document sections and generates accurate answers based on the retrieved context.",
    instruction="""
        You are a Document RAG Agent specialized in answering questions based on retrieved document content. Follow this workflow:

        1. Document Retrieval  
        Use the `search_similar_ads` tool to retrieve relevant document sections using the provided optimized query.
    

        2. Context Analysis  
        Carefully analyze the retrieved document sections to understand the context and relevant information.

        3. Answer Generation  
        - Provide accurate answers based solely on the retrieved document content
        - If the information is not in the retrieved context, clearly state that you don't have that information in the documents
        - Cite the source when possible (mention document name or section)
        - Be concise but comprehensive
        - Use clear, easy-to-understand language

        4. Response Format  
        Structure your response as follows:
        - Direct answer to the question
        - Supporting details from the documents
        - Source reference if available

        5. Best Practices  
        - Stay faithful to the document content - do not make up information
        - If multiple documents provide different information, acknowledge this
        - If the question cannot be answered from the documents, say so clearly
        - Maintain a helpful and professional tone

        6. No Results Handling  
        If no relevant information found:  
        "I couldn't find relevant information in the documents to answer your question. Please try rephrasing or ask about a different topic covered in the documents."
    """,
    tools=[search_tool],
    output_key="final_response",
    before_agent_callback= opik_tracer.before_agent_callback,
    after_agent_callback=opik_tracer.after_agent_callback, 
    before_model_callback=opik_tracer.before_model_callback,
    after_model_callback=opik_tracer.after_model_callback,
    before_tool_callback=opik_tracer.before_tool_callback,
    after_tool_callback=opik_tracer.after_tool_callback,
)


# Create session service and session
session_service = InMemorySessionService()

from uuid import uuid4
APP_NAME = "document-chat-ai" 
USER_ID = "user_1"
SESSION_ID = "uuid4().hex"  # Generate a unique session ID

# Create the specific session where the conversation will happen
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)
print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

# Create the runner
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)
print(f"Runner created for agent '{runner.agent.name}'.")

async def generate_response(query: str):
    """Sends a natural language query to the agent and returns the response."""
    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."  # default

    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:  # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break

    print(f"<<< Agent Response: {final_response_text}")
    return final_response_text


async def call_agent_async(query: str, session_id: str= SESSION_ID, user_id: str=USER_ID):
    """
    Call the agent using Google ADK API
    
    Returns:
        str: The agent's response text
        dict: Error dictionary if the agent callback raised an exception
    """
     
    try:
        # Ensure user_id is not None
        safe_user_id = user_id or USER_ID
        
        # First, try to get existing session from ADK
        session = None
        try:
            session = await session_service.get_session(
                app_name=APP_NAME,
                user_id=safe_user_id,
                session_id=session_id
            )
        except Exception as e:
            print(f"Session {session_id} not found, creating new one: {e}")
            
        # Create session if it doesn't exist in ADK
        if session is None:
            try:
                session = await session_service.create_session(
                    app_name=APP_NAME,
                    user_id=safe_user_id,
                    session_id=session_id
                )
                print(f"Created new ADK session: {session_id} for user: {safe_user_id}")
            except Exception as e:
                print(f"Failed to create session {session_id}: {e}")
                return f"Error creating session: {str(e)}"
        
        # Prepare the user's message in ADK format
        content = types.Content(role='user', parts=[types.Part(text=query)])
        
        response_text = "I apologize, but I couldn't process your request."
        
        # Use run_async with proper parameters
        async for event in runner.run_async(
            user_id=safe_user_id or USER_ID, 
            session_id=session_id, 
            new_message=content
        ):
            print(f"Event received: type={type(event)}, is_final={event.is_final_response()}")
            
            # Append event to session to maintain conversation history
            if session:
                try:
                    await session_service.append_event(session=session, event=event)
                except Exception as e:
                    print(f"Failed to append event to session: {e}")
            
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    # break
                    
        return response_text
    
    
        
    except Exception as e:
        print(f"ADK call_agent_async error: {e}")
        return f"Error processing request: {str(e)}"