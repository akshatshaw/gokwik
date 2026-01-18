from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Tool: DuckDuckGo Web Search
def duckduckgo_search_tool(query: str) -> str:
    try:
        search = DuckDuckGoSearchRun()
        results = search.run(query)
        return f"🔍 DuckDuckGo Search Results for '{query}':\n\n{results}"
    except Exception as e:
        return f"Search failed: {str(e)}\n\nFallback results:\n- Information about {query}\n- Documentation on {query}"


# Tool: Wikipedia Search
def wikipedia_search_tool(query: str) -> str:
    try:
        wikipedia = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=2000)
        results = wikipedia.run(query)
        return f"📚 Wikipedia Results for '{query}':\n\n{results}"
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}\n\nFallback: No Wikipedia results for {query}"


# Agent: Summarizer using real LLM with custom system prompt
def create_summarizer_agent(system_prompt: str, llm_instance: ChatOpenAI):
    def summarizer_agent(input_text: str) -> str:
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Please summarize or answer the following:\n\n{input_text}")
            ]
            response = llm_instance.invoke(messages)
            return response.content
        except Exception as e:
            if len(input_text) > 300:
                summary = input_text[:297] + "..."
            else:
                summary = input_text
            return f"SUMMARY (Fallback):\n{summary}\n\n[LLM Error: {str(e)}]"
    return summarizer_agent


# Build runnables
duckduckgo_runnable = RunnableLambda(duckduckgo_search_tool)
wikipedia_runnable = RunnableLambda(wikipedia_search_tool)


class WorkflowRequest(BaseModel):
    user_input: str
    connected: bool
    tool: Optional[str] = None
    system_prompt: Optional[str] = "You are a helpful assistant that provides clear, concise summaries. Keep your response under 200 words."
    model: Optional[str] = "gpt-3.5-turbo"


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/run")
async def run_workflow(req: WorkflowRequest):
    try:
        # Create agent with custom system prompt
        llm = ChatOpenAI(
            model=req.model,
        )
        agent_fn = create_summarizer_agent(req.system_prompt, llm_instance=llm)
        agent_runnable = RunnableLambda(agent_fn)
        
        if req.connected and req.tool:
            # Select the appropriate tool
            if req.tool == "wikipedia":
                tool_runnable = wikipedia_runnable
            else:
                tool_runnable = duckduckgo_runnable
            
            # Tool → Agent pipeline using LangChain Runnables
            chain = tool_runnable | agent_runnable
            result = chain.invoke(req.user_input)
        else:
            # Agent only
            result = agent_runnable.invoke(req.user_input)
        
        return JSONResponse({"success": True, "output": result})
    except Exception as e:
        return JSONResponse({"success": False, "output": f"Error: {str(e)}"}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
