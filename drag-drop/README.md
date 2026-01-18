# Drag & Drop Agentic UI Prototype

A simple, visual workflow builder that lets non-technical users connect an AI agent to a web search tool and execute workflows through a drag-and-drop interface.

## Features

- **Visual Canvas**: Drag and position nodes freely on the canvas
- **Connection System**: Click "Connect Nodes" to wire Tool → Agent pipeline
- **Real Web Search**: Uses DuckDuckGo search (no API key needed)
- **AI Summarizer**: GPT-3.5 powered agent that summarizes search results
- **Real-time Feedback**: Visual status indicators and animated connections
- **Clean UI**: Modern, responsive design with gradient backgrounds

## Tech Stack

- **Backend**: FastAPI (Python)
- **Agent Framework**: LangChain Runnables
- **LLM**: OpenAI GPT-3.5-turbo
- **Tool**: DuckDuckGo Search (via langchain-community)
- **Frontend**: Pure HTML/CSS/JavaScript (no frameworks)

## Setup Instructions

### 1. Install Dependencies

This project uses `uv` for fast Python package management:

```bash
# Dependencies are already installed if you've run the setup
uv sync
```

### 2. Configure OpenAI API Key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Run the Application

```bash
uv run uvicorn app:app --reload
```

The app will be available at: http://127.0.0.1:8000

## How to Use

1. **Open the app** in your browser at http://127.0.0.1:8000

2. **Drag the nodes** to position them as you like on the canvas

3. **Connect the workflow**:
   - Click the "Connect Nodes" button
   - You'll see an animated connection line between Tool → Agent
   - Status indicator turns green

4. **Enter a query**:
   - Type your question in the text area (e.g., "artificial intelligence trends 2026")

5. **Run the workflow**:
   - Click "Run Workflow"
   - The system will:
     - Search the web using DuckDuckGo
     - Pass results to the AI agent
     - Display the summary in the output box

6. **Disconnect** (optional):
   - Click "Disconnect" to break the connection
   - Running the workflow will now only use the Agent (no search)

## Execution Flow

### Connected Mode (Tool → Agent):

```
User Input → Web Search Tool → Search Results → AI Agent → Summary Output
```

### Disconnected Mode (Agent Only):

```
User Input → AI Agent → Direct Response
```

## Project Structure

```
drag-drop/
├── app.py                 # FastAPI backend with LangChain
├── .env                   # Environment variables (API keys)
├── .env.example          # Template for environment file
├── pyproject.toml        # Project dependencies (uv)
├── static/
│   ├── css/
│   │   └── style.css     # Modern, responsive styling
│   └── js/
│       └── app.js        # Drag-and-drop + connection logic
└── templates/
    └── index.html        # Main UI template
```

## Key Implementation Details

### Backend (app.py)

- **Web Search Tool**: Uses `DuckDuckGoSearchRun` for real web searches
- **AI Agent**: Uses `ChatOpenAI` with GPT-3.5-turbo
- **Dynamic Pipeline**: Builds `RunnableSequence` based on connection state
- **Error Handling**: Fallback mechanisms if LLM or search fails

### Frontend

- **Drag System**: Pure JavaScript with boundary constraints
- **Connection Drawing**: SVG paths with cubic Bezier curves
- **Status Management**: Real-time visual feedback
- **Responsive**: Works on desktop and mobile

## Limitations & Notes

- Requires OpenAI API key (costs apply per API call)
- DuckDuckGo search is free but may have rate limits
- Simple UI optimized for clarity over features
- Single tool and agent (extensible for more)

## Future Enhancements

- Add more tools (SQLite, Email, File operations)
- Multiple agents (Q&A, Code Generator, etc.)
- Save/load workflows
- Real drag-to-connect between ports
- Workflow execution history
- Custom tool/agent configuration

## Troubleshooting

**Error: "Import langchain_community could not be resolved"**

- Run `uv sync` to ensure all packages are installed

**Error: "Invalid API key"**

- Check your `.env` file has the correct `OPENAI_API_KEY`
- Restart the server after updating `.env`

**Search returns fallback results**

- DuckDuckGo search may fail occasionally
- Fallback provides mock results so workflow continues

**UI not loading styles**

- Check that `static/css/style.css` and `static/js/app.js` exist
- Clear browser cache and refresh

## License

MIT License - Feel free to use and modify!
